from datetime import date
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import (Column, Date, ForeignKey, Integer, String, create_engine,
                        func)
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

DATABASE_URL = "sqlite:///./league.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # scorer, captain, player


class Series(Base):
    __tablename__ = "series"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    captain_id = Column(Integer, ForeignKey("users.id"), nullable=False)


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)


class Round(Base):
    __tablename__ = "rounds"

    id = Column(Integer, primary_key=True)
    series_id = Column(Integer, ForeignKey("series.id"), nullable=False)
    name = Column(String, nullable=False)


class TeamPoint(Base):
    __tablename__ = "team_points"

    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    points = Column(Integer, nullable=False, default=0)


class PlayerPerformance(Base):
    __tablename__ = "player_performance"

    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    performance_points = Column(Integer, nullable=False, default=0)
    is_man_of_match = Column(Integer, nullable=False, default=0)


Base.metadata.create_all(bind=engine)


def ensure_default_scorer():
    db = SessionLocal()
    try:
        any_user = db.query(User).first()
        if not any_user:
            db.add(User(id=1, name="Default Scorer", role="scorer"))
            db.commit()
    finally:
        db.close()


ensure_default_scorer()

app = FastAPI(title="Series Points API")


class UserIn(BaseModel):
    name: str
    role: str = Field(pattern="^(scorer|captain|player)$")


class SeriesIn(BaseModel):
    name: str
    start_date: date
    end_date: date


class TeamIn(BaseModel):
    name: str
    captain_id: int


class MemberIn(BaseModel):
    user_id: int
    team_id: int


class RoundIn(BaseModel):
    series_id: int
    name: str


class TeamPointsIn(BaseModel):
    round_id: int
    team_id: int
    points: int


class PlayerPerformanceIn(BaseModel):
    round_id: int
    player_id: int
    performance_points: int
    is_man_of_match: bool = False


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_actor(x_user_id: Optional[int] = Header(default=None), db: Session = Depends(get_db)):
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="x-user-id header is required")
    actor = db.get(User, x_user_id)
    if not actor:
        raise HTTPException(status_code=401, detail="invalid x-user-id")
    return actor


def require_updater(actor: User):
    if actor.role != "scorer":
        raise HTTPException(status_code=403, detail="only scorer users can update data")


@app.post("/users")
def create_user(payload: UserIn, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    require_updater(actor)
    if payload.role == "scorer":
        scorer_count = db.query(func.count(User.id)).filter(User.role == "scorer").scalar() or 0
        if scorer_count >= 6:
            raise HTTPException(status_code=400, detail="max 6 scorer users allowed")
    user = User(name=payload.name, role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "name": user.name, "role": user.role}


@app.post("/series")
def create_series(payload: SeriesIn, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    require_updater(actor)
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="end_date must be >= start_date")
    if (payload.end_date - payload.start_date).days > 92:
        raise HTTPException(status_code=400, detail="series period cannot exceed 3 months")
    series = Series(name=payload.name, start_date=payload.start_date, end_date=payload.end_date)
    db.add(series)
    db.commit()
    db.refresh(series)
    return {"id": series.id, "name": series.name}


@app.post("/teams")
def create_team(payload: TeamIn, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    require_updater(actor)
    captain = db.get(User, payload.captain_id)
    if not captain or captain.role != "captain":
        raise HTTPException(status_code=400, detail="captain_id must be a valid captain")
    team = Team(name=payload.name, captain_id=payload.captain_id)
    db.add(team)
    db.commit()
    db.refresh(team)
    return {"id": team.id, "name": team.name}


@app.post("/members")
def add_member(payload: MemberIn, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    require_updater(actor)
    user = db.get(User, payload.user_id)
    team = db.get(Team, payload.team_id)
    if not user or user.role not in {"captain", "player"}:
        raise HTTPException(status_code=400, detail="user must be captain or player")
    if not team:
        raise HTTPException(status_code=404, detail="team not found")
    member = Member(user_id=payload.user_id, team_id=payload.team_id)
    db.add(member)
    db.commit()
    db.refresh(member)
    return {"id": member.id}


@app.post("/rounds")
def create_round(payload: RoundIn, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    require_updater(actor)
    series = db.get(Series, payload.series_id)
    if not series:
        raise HTTPException(status_code=404, detail="series not found")
    round_ = Round(series_id=payload.series_id, name=payload.name)
    db.add(round_)
    db.commit()
    db.refresh(round_)
    return {"id": round_.id, "name": round_.name}


@app.post("/team-points")
def update_team_points(payload: TeamPointsIn, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    require_updater(actor)
    record = TeamPoint(round_id=payload.round_id, team_id=payload.team_id, points=payload.points)
    db.add(record)
    db.commit()
    return {"status": "ok"}


@app.post("/player-performance")
def update_player_performance(payload: PlayerPerformanceIn, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    require_updater(actor)
    perf = PlayerPerformance(
        round_id=payload.round_id,
        player_id=payload.player_id,
        performance_points=payload.performance_points,
        is_man_of_match=1 if payload.is_man_of_match else 0,
    )
    db.add(perf)
    db.commit()
    return {"status": "ok"}


@app.get("/rounds/{round_id}/man-of-match")
def man_of_match(round_id: int, _: User = Depends(get_actor), db: Session = Depends(get_db)):
    winner = (
        db.query(PlayerPerformance)
        .filter(PlayerPerformance.round_id == round_id)
        .order_by(PlayerPerformance.is_man_of_match.desc(), PlayerPerformance.performance_points.desc())
        .first()
    )
    if not winner:
        raise HTTPException(status_code=404, detail="no performance data")
    player = db.get(User, winner.player_id)
    return {"round_id": round_id, "player_id": player.id, "player_name": player.name}


@app.get("/series/{series_id}/standings")
def series_results(series_id: int, _: User = Depends(get_actor), db: Session = Depends(get_db)):
    series = db.get(Series, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="series not found")

    rounds = db.query(Round.id).filter(Round.series_id == series_id).subquery()

    team_totals = (
        db.query(Team.id, Team.name, func.sum(TeamPoint.points).label("total_points"))
        .join(TeamPoint, Team.id == TeamPoint.team_id)
        .filter(TeamPoint.round_id.in_(rounds))
        .group_by(Team.id)
        .order_by(func.sum(TeamPoint.points).desc())
        .all()
    )
    winner_team = team_totals[0] if team_totals else None

    player_totals = (
        db.query(User.id, User.name, func.sum(PlayerPerformance.performance_points).label("total_points"))
        .join(PlayerPerformance, User.id == PlayerPerformance.player_id)
        .filter(PlayerPerformance.round_id.in_(rounds))
        .group_by(User.id)
        .order_by(func.sum(PlayerPerformance.performance_points).desc())
        .all()
    )
    mos = player_totals[0] if player_totals else None

    return {
        "series_id": series_id,
        "winner_team": None if not winner_team else {"team_id": winner_team.id, "team_name": winner_team.name, "points": int(winner_team.total_points or 0)},
        "man_of_the_series": None if not mos else {"player_id": mos.id, "player_name": mos.name, "points": int(mos.total_points or 0)},
        "team_table": [
            {"team_id": row.id, "team_name": row.name, "points": int(row.total_points or 0)} for row in team_totals
        ],
    }

# Series Points Management API

This is a lightweight FastAPI backend for a tournament/series point table.

It supports your requested rules:

- Up to **6 scorer users** can update data.
- **Captains and players are view-only**.
- Series duration is limited to **3 months (92 days)**.
- Calculates:
  - **Man of the Match** per round
  - **Winner Team** at series end
  - **Man of the Series** at series end

---

## 1) Download the project

### Option A: If you use Git

```bash
git clone <your-repo-url>
cd Sid
```

### Option B: Without Git (easy for other users)

1. Open repository in browser.
2. Click **Code** → **Download ZIP**.
3. Extract ZIP.
4. Open terminal in extracted folder.

---

## 2) Run locally on Windows

### Prerequisites

- Python 3.10+ installed from [python.org](https://www.python.org/downloads/)
- During install, check **"Add Python to PATH"**

### PowerShell commands

```powershell
cd C:\path\to\Sid
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Open docs:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 3) Run on Linux / macOS

```bash
cd /path/to/Sid
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

---

## 4) Let other users on your network use it

If your PC/server IP is `192.168.1.20`, users on same Wi-Fi/LAN can open:

- `http://192.168.1.20:8000/docs`

Important:

- Keep `--host 0.0.0.0` in uvicorn command.
- Allow inbound TCP **8000** in firewall.
- Keep machine running while users access.

---

## 5) Run with Docker (good for sharing)

This repo includes a `Dockerfile`.

```bash
docker build -t series-points-api .
docker run -p 8000:8000 series-points-api
```

Then open `http://localhost:8000/docs`.

For another user: publish on a server and share server IP/domain.

---

## 6) Minimal auth/roles behavior

Every request needs header: `x-user-id`.

- `scorer` → can create/update records
- `captain` / `player` → read-only APIs

Default bootstrap user is auto-created:

- `id = 1`
- `name = Default Scorer`
- `role = scorer`

So initially, send:

```http
x-user-id: 1
```

---

## 7) API flow (recommended)

1. `POST /users` → create captains, players, extra scorers (max 6 scorers total)
2. `POST /series` → create a series (<= 92 days)
3. `POST /teams` → create teams with captain IDs
4. `POST /members` → add captain/player users into teams
5. `POST /rounds` → create rounds
6. `POST /team-points` + `POST /player-performance` each round
7. `GET /rounds/{round_id}/man-of-match`
8. `GET /series/{series_id}/standings`

---

## 8) Deploy so anyone can use it online

To let users outside your local network access it 24/7, deploy on a cloud host:

- Render, Railway, Fly.io, Azure, AWS, GCP, DigitalOcean, etc.

Typical steps:

1. Push repo to GitHub.
2. Create web service in host.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Share generated HTTPS URL.

---

## 9) Notes for production

Current app uses SQLite (`league.db`) and very simple header auth for prototyping.

For production/many concurrent users, add:

- PostgreSQL/MySQL instead of SQLite
- proper login/auth (JWT/OAuth)
- HTTPS, backups, audit logs
- input validation and duplicate constraints
- role management UI/frontend

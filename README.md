# CA Firm Manager (Ready-to-use, No Dependency)

This repository now includes a **single-file web app** (`index.html`) that runs directly in your browser with **zero install**.

## What it provides

- Client master management
- Assignment tracking (due dates, owner, status, progress)
- Billing and payment status
- Reminders
- Bulk upload with preview, validation, duplicate detection, error rows, and commit
- Audit logs

## No dependency usage

1. Open `index.html` in any modern browser (Chrome/Edge/Firefox).
2. Start using the app immediately.
3. All data is saved in browser `localStorage`.

> Tip: For bulk upload, prepare your sheet in Excel and save it as CSV.

## Bulk upload template (CSV)

```csv
client_code,client_name,entity_type,pan,gstin,email,phone,assigned_partner,assigned_manager,status
```

## Notes

- This is a front-end-only local app.
- Data is device/browser specific (because it is stored in localStorage).
- Use **Audit Logs > Reset All Data** to clear all records.

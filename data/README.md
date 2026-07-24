# data

Runtime data lives here. The SQLite database and uploaded floor plans land
under this directory so they're easy to find, easy to back up, and easy to
.gitignore (see the top-level `.gitignore`).

```
data/
├── db/                    # SQLite files (*.sqlite) — gitignored
└── uploads/               # uploaded floor plans — gitignored
```

Nothing in this directory should be committed. To rebuild the database from
scratch:

```bash
cd backend
python -m dazuoagent.db.seed
```
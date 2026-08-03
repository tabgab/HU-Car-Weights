# Database backup

`cars.db.gz` is a gzip of a consistent snapshot of the built SQLite database
(`data/cars.db`), taken with SQLite's online backup API.

Restore:
```bash
gunzip -c backups/cars.db.gz > data/cars.db
```

The snapshot is self-contained — no `-wal`/`-shm` sidecar is needed, and it is safe to
take while the app or a scrape is running. Do **not** hand-roll it as `gzip -c
data/cars.db`: the DB runs in WAL mode, so committed rows can live only in
`data/cars.db-wal` and copying the main file alone silently loses them.

The DB is regenerable from the scraper (`carweights.cli market`, `hu`, `dealer`,
`omodajaecoo`, `extra-hu`) but that takes hours of polite crawling, so this snapshot
is the quick way to get a working dataset. Refresh it with `./backups/refresh.sh`.

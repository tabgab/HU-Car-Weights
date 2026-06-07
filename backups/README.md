# Database backup

`cars.db.gz` is a gzip of the built SQLite database (`data/cars.db`).

Restore:
```bash
gunzip -c backups/cars.db.gz > data/cars.db
```

The DB is regenerable from the scraper (`carweights.cli market`, `hu`, `dealer`,
`omodajaecoo`, `extra-hu`) but that takes hours of polite crawling, so this snapshot
is the quick way to get a working dataset. Refresh it with `./backups/refresh.sh`.

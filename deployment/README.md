# Local deployment

The systemd units in this directory are examples for the owner's Linux host.
They are intentionally machine-specific because they point to the local
checkout and virtual environment. Review the paths before installing them.

Runtime secrets and state belong in `~/.job-finder/`, especially:

- `secrets.env` for API keys and notification credentials;
- `state.db` for SQLite state;
- logs and health snapshots;
- the persistent browser profile used by the optional LinkedIn integration.

GitHub Actions validates the repository only. These local services are the
production runtime for this personal installation.

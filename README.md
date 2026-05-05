# cronwatch

Lightweight daemon that monitors cron job execution and sends alerts on failures or missed runs.

---

## Installation

```bash
pip install cronwatch
```

Or install from source:

```bash
git clone https://github.com/youruser/cronwatch.git && cd cronwatch && pip install .
```

---

## Usage

Define your monitored jobs in `cronwatch.yaml`:

```yaml
jobs:
  daily-backup:
    schedule: "0 2 * * *"
    timeout: 300
    alert: email
  cleanup-logs:
    schedule: "*/15 * * * *"
    timeout: 60
    alert: slack
```

Start the daemon:

```bash
cronwatch start --config cronwatch.yaml
```

Wrap an existing cron command to report its status:

```bash
cronwatch run --job daily-backup -- /usr/local/bin/backup.sh
```

Check status of all monitored jobs:

```bash
cronwatch status
```

---

## Configuration

| Key        | Description                              | Default  |
|------------|------------------------------------------|----------|
| `schedule` | Cron expression for expected run time    | required |
| `timeout`  | Max allowed runtime in seconds           | `60`     |
| `alert`    | Alert channel (`email`, `slack`, `webhook`) | `email` |

---

## License

MIT © 2024 cronwatch contributors
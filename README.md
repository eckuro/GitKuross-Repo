# Oslo Insider Alerts

A monitoring system that tracks and alerts on heavy insider trading activity for small and medium-sized companies listed on the Oslo Stock Exchange (Oslo Børs, Euronext Expand, and Euronext Growth).

## Features

- **Real-time Monitoring**: Fetches insider trading announcements from Oslo Børs NewsWeb
- **Smart Filtering**: Focuses on small and medium-cap companies (configurable thresholds)
- **Multiple Alert Types**:
  - Large single transactions (value threshold)
  - High percentage of outstanding shares traded
  - Aggregate insider activity within time windows
  - Cluster detection (multiple insiders trading in same direction)
  - Direction changes (insider reverses from buying to selling or vice versa)
- **Flexible Notifications**: Console, Email, and Slack support
- **Persistent Storage**: SQLite database for tracking historical data
- **Configurable Thresholds**: All alert parameters are configurable

## Installation

### Using pip

```bash
# Clone the repository
git clone https://github.com/your-org/oslo-insider-alerts.git
cd oslo-insider-alerts

# Install with pip
pip install -e .

# Or with optional dependencies for notifications
pip install -e ".[notifications]"

# For development
pip install -e ".[dev]"
```

### Using uv (recommended)

```bash
uv pip install -e ".[notifications]"
```

## Quick Start

1. **Generate a configuration template:**

```bash
oslo-insider config-template > .env
```

2. **Edit the configuration** (optional - defaults work for basic usage):

```bash
# Edit .env to customize thresholds and notifications
```

3. **Run a one-time check:**

```bash
oslo-insider run --days 7
```

4. **Run continuously:**

```bash
oslo-insider run --continuous
```

## Configuration

Configuration can be done via environment variables or a `.env` file. Here are the key settings:

### Alert Thresholds

| Variable | Default | Description |
|----------|---------|-------------|
| `ALERT_MIN_TRANSACTION_VALUE_NOK` | 500,000 | Minimum single transaction value to alert |
| `ALERT_MIN_SHARES_PERCENT` | 0.1 | Minimum % of outstanding shares for alert |
| `ALERT_AGGREGATE_VALUE_NOK` | 2,000,000 | Aggregate value threshold within time window |
| `ALERT_AGGREGATE_WINDOW_DAYS` | 7 | Time window for aggregate calculations |
| `ALERT_MIN_INSIDER_COUNT` | 2 | Minimum insiders for cluster alert |

### Company Size Filter

| Variable | Default | Description |
|----------|---------|-------------|
| `COMPANY_SMALL_CAP_MAX_NOK_BILLIONS` | 5.0 | Max market cap for small-cap (NOK billions) |
| `COMPANY_MEDIUM_CAP_MAX_NOK_BILLIONS` | 25.0 | Max market cap for medium-cap (NOK billions) |
| `COMPANY_INCLUDE_TICKERS` | [] | Always include these tickers |
| `COMPANY_EXCLUDE_TICKERS` | [] | Always exclude these tickers |

### Notifications

| Variable | Description |
|----------|-------------|
| `NOTIFY_CHANNELS` | List of channels: `["console", "email", "slack"]` |
| `NOTIFY_SLACK_WEBHOOK_URL` | Slack incoming webhook URL |
| `NOTIFY_SLACK_CHANNEL` | Slack channel name |
| `NOTIFY_EMAIL_SMTP_HOST` | SMTP server hostname |
| `NOTIFY_EMAIL_TO` | List of recipient emails |

## CLI Commands

### `oslo-insider run`

Fetch and process insider transactions.

```bash
# One-time run, last 7 days
oslo-insider run --days 7

# Continuous monitoring
oslo-insider run --continuous

# With custom config
oslo-insider run --config /path/to/config.env
```

### `oslo-insider check`

View recent insider activity.

```bash
# All recent transactions
oslo-insider check --days 30

# For a specific company
oslo-insider check --ticker AKER
```

### `oslo-insider stats`

Show statistics about tracked activity.

```bash
oslo-insider stats
```

### `oslo-insider test-alert`

Send a test alert to verify notification setup.

```bash
oslo-insider test-alert
```

## Alert Types

### 1. Large Single Transaction
Triggered when a single insider transaction exceeds the value threshold.

**Severity levels:**
- LOW: 1-2x threshold
- MEDIUM: 2-5x threshold
- HIGH: 5-10x threshold
- CRITICAL: 10x+ threshold

### 2. High Percentage Trade
Triggered when a transaction represents a significant percentage of outstanding shares.

### 3. Aggregate Activity
Triggered when total insider buying or selling within the time window exceeds the aggregate threshold.

### 4. Insider Cluster
Triggered when multiple insiders trade in the same direction (all buying or all selling).

### 5. Direction Change
Triggered when an insider reverses their trading direction (e.g., was selling, now buying).

## Data Sources

The system fetches data from:
- **Oslo Børs NewsWeb**: Primary source for insider trading announcements (PDMR notifications)
- Covers: Oslo Børs, Euronext Expand (formerly Oslo Axess), Euronext Growth Oslo

## Architecture

```
oslo_insider_alerts/
├── __init__.py          # Package initialization
├── app.py               # Main application orchestrator
├── cli.py               # Command-line interface
├── config.py            # Configuration management
├── models.py            # Data models (Pydantic)
├── fetcher.py           # Oslo Børs data fetcher
├── classifier.py        # Company size classification
├── rules.py             # Alert rules engine
├── notifications.py     # Notification channels
└── database.py          # SQLite persistence layer
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy oslo_insider_alerts

# Linting
ruff check oslo_insider_alerts
```

## Legal Notice

This tool is designed for legitimate financial monitoring and research purposes. Insider trading data used by this system is publicly available regulatory information published by Oslo Børs.

Users are responsible for complying with all applicable laws and regulations regarding the use of this information.

## License

MIT License - see LICENSE file for details.

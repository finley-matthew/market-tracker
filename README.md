# market-tracker

A small Python service that collects market data on a schedule: the gold spot price every hour from a public API, and the US 10-year minus 2-year Treasury yield spread from the Federal Reserve's FRED API. It runs under cron on Ubuntu (WSL) and logs every run in a fixed format so it can be monitored.

The operations side of this project (health checks, gap detection and incident write-ups) lives in a separate repo: [infra-labs](https://github.com/finley-matthew/infra-labs).

## Scripts

| Script | What it does | Data format |
|---|---|---|
| `live_price.py` | Fetches the current gold price (XAU) from the [Gold API](https://gold-api.com) and logs the result. This is the scheduled job. | JSON |
| `fred_spread.py` | Fetches the latest 10Y-2Y Treasury spread (series `T10Y2Y`) from FRED, skipping days with no value. | JSON |
| `fred_xml.py` | The same FRED request, but asking for and parsing XML instead. | XML |
| `tracker.py` | First exercise: reads and prints prices from a local sample file, `sample_price.json`. | JSON |

## What it demonstrates

- **Calling REST APIs** with `requests`, with a 5-second timeout on every request, and parsing both JSON and XML responses.
- **Error handling by failure type.** In `live_price.py`, HTTP 4xx and 5xx responses are logged as `ClientError` and `ServerError` with the status code. Timeouts, connection errors and other request failures are caught separately, so the log shows *where* a failure happened (for example `ReadTimeout`: connected, but the server was slow, versus `ConnectTimeout`: couldn't connect at all). The FRED scripts report any non-200 status code to stderr and exit with code 1.
- **Logging designed to be parsed.** Every run of `live_price.py` writes exactly one line to `tracker.log`, in a fixed field order (see [Log format](#log-format)).
- **Scheduling with cron**, including the environment problems cron causes (see [Scheduling](#scheduling)).
- **Keeping secrets out of Git and out of output** (see [Security](#security)).
- **Dependency maintenance**: all dependencies pinned, and a patch applied with a tested rollback plan (see [Maintenance](#maintenance)).

## Setup

Tested on Python 3.14, Ubuntu on WSL.

```bash
git clone https://github.com/finley-matthew/market-tracker.git
cd market-tracker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The FRED scripts need a free API key from [FRED](https://fred.stlouisfed.org/docs/api/api_key.html). Put it in a `.env` file in the project folder (already ignored by Git):

```
FRED_KEY=your_key_here
```

## Usage

```bash
python3 live_price.py      # prints the price and appends one line to tracker.log
python3 fred_spread.py     # prints "10Y-2Y spread: <value>% (<date>)"
python3 fred_xml.py        # same result, via XML
```

The FRED scripts write errors to stderr and exit with code 1 on any failure, so a caller (or cron) can tell success from failure.

## Log format

`live_price.py` appends one line per run to `tracker.log`:

```
2026-10-07 10:00:01,366 INFO XAU 4142.3
2026-10-06 10:00:06,021 ERROR Timeout XAU ConnectTimeout
```

| Field | Content |
|---|---|
| 1–2 | Date and time |
| 3 | Level: `INFO` for a successful run, `ERROR` for a failure |
| 4 | On success, the symbol. On failure, the error type (`Timeout`, `ConnectionError`, `ClientError`, `ServerError`, `RequestException`) |
| 5+ | On success, the price. On failure, the symbol and detail (exception class or HTTP status code) |

The fixed layout is what lets the tools in [infra-labs](https://github.com/finley-matthew/infra-labs) count successes, group errors by type and find missing runs.

## Scheduling

`live_price.py` runs hourly under cron. The entry is kept in [`crontab.txt`](crontab.txt):

```
0 * * * * cd /path/to/market-tracker && /path/to/market-tracker/.venv/bin/python live_price.py >> cron.log 2>&1
```

- **`cd` first**, because cron starts jobs in the home folder, and the script writes `tracker.log` relative to where it runs.
- **The venv's Python by full path**, because cron doesn't activate the venv. The system Python doesn't have this project's dependencies installed.
- **`>> cron.log 2>&1`** sends both normal output and errors (such as a Python traceback) to `cron.log`, so a crash leaves evidence.

**Known limitation:** cron runs inside WSL, so the job only runs while the PC is on. This caused a six-hour gap on 13 October, written up in [infra-labs](https://github.com/finley-matthew/infra-labs/blob/main/incidents/2026-10-13-scheduler-host-offline.md). Moving to an always-on host is on the roadmap.

## Security

- The FRED API key lives in `.env`, which is listed in `.gitignore` along with the venv and log files. The key has never been committed.
- During development, an unhandled connection error printed the full request URL, **including the API key**, to the terminal. Nothing was committed, but since then the request error handlers print only the exception's class name (`type(e).__name__`), never the exception itself, because its message can contain the URL.
- `fred_xml.py` does print the full `ParseError` message, deliberately: the parser only ever sees the response body, which doesn't contain the key.

## Maintenance

- **Dependencies are pinned** with `==` in `requirements.txt`, so every install gets the same versions.
- **Patching:** `charset-normalizer` (a dependency of `requests`) was updated from 3.5.1 to 3.5.2. Process: checked `pip list --outdated`, saved a `pip freeze` snapshot, installed the exact new version, re-ran the scripts, compared before and after with `diff` (one line changed), then updated the pin. Rollback: reinstall `charset-normalizer==3.5.1` and restore `requirements.txt` with `git restore`.
- **Style:** Python code is checked with `pycodestyle` (line limit 99, set in `setup.cfg`).

## Roadmap

The aim is to turn this from a single price logger into a small data service that pulls related data from several sources, stores it, and compares them. Planned work, roughly in this order:

### 1. Foundations

- **Store every reading in SQLite** instead of only logging it, so series from different sources can be lined up by date and compared.
- **Restructure the code**: one module per data source, shared request and error handling, a `main()` entry point and a config file listing which series to collect.
- **Tests with `pytest`**, run by **GitHub Actions** on every push alongside `pycodestyle`.
- **Run the jobs as systemd services and timers** instead of cron, with logs in `journalctl`.
- **Retry with backoff** after a timeout, and alert only after consecutive failures.

### 2. More data sources

| Data | Source | Format and update rate | Access |
|---|---|---|---|
| Silver price (XAG) | Gold API | JSON, on request | No key |
| Brent crude oil price | FRED (`DCOILBRENTEU`) | JSON, daily | API key |
| US dollar / pound exchange rate | FRED | JSON, daily | API key |
| More US Treasury spreads, e.g. 10-year minus 3-month (`T10Y3M`) | FRED | JSON, daily | API key |
| US 10-year real (inflation-adjusted) yield (`DFII10`) | FRED | JSON, daily | API key |
| UK average petrol and diesel pump prices | GOV.UK weekly road fuel prices | CSV, weekly | None |
| Local forecourt fuel prices | GOV.UK Fuel Finder API | JSON, within 30 minutes of a price change | OAuth 2.0 client credentials |
| UK gilt yields | Bank of England database | To be confirmed | To be confirmed |
| UK inflation (CPI) | ONS | To be confirmed | To be confirmed |

Each source fails in its own way, and each new one gets the same error handling, logging and health checks as the gold price.

### 3. Comparisons and charts

- **Crude oil vs UK fuel prices.** Convert Brent from US dollars per barrel to pence per litre, then chart it against UK pump prices. Questions: how long do pump prices take to follow crude, do they fall as quickly as they rise, and how much of a litre's price is crude versus tax? Then compare local forecourt prices against the national average.
- **Treasury yield spreads over time**, with a zero line and periods of inversion shaded, comparing 10Y-2Y with 10Y-3M.
- **Gold vs US real yields**, to test the often-cited inverse relationship with my own data.
- **Gold in dollars vs gold in pounds**, to separate gold's own moves from currency moves.
- **Gold/silver ratio** against its long-run average.
- **UK gilt yields vs US Treasury yields**, and **UK inflation vs gilt yields**.
- **Daily summary**: open, close, high, low and percentage change for each series.

### 4. Serving and deployment

- **A small JSON API** serving the stored history.
- **Package it in Docker.**
- **Move it to an always-on AWS EC2 instance**, defined in **Terraform**, with CloudWatch alarms and database backups to S3. This removes the dependency on my PC being switched on.

Before building on any new source, I check its terms of use and licensing.

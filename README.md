# market-tracker

A small Python project that collects market data on a schedule. Every hour it fetches the gold spot price from a public API, and it can also pull the US 10-year minus 2-year Treasury yield spread from the Federal Reserve's FRED API. It runs under cron on Ubuntu (WSL) and logs each run so I can monitor it.

The monitoring tools and incident write-ups live in a separate repo, [infra-labs](https://github.com/finley-matthew/infra-labs).

## Scripts

| Script | What it does | Format |
|---|---|---|
| `live_price.py` | Fetches the gold price (XAU) from the [Gold API](https://gold-api.com) and logs the result. This is the scheduled job. | JSON |
| `fred_spread.py` | Fetches the latest 10Y-2Y Treasury spread (`T10Y2Y`) from FRED, skipping days with no value. | JSON |
| `fred_xml.py` | The same FRED request, parsed as XML instead. | XML |
| `tracker.py` | My first exercise: prints prices from a local file, `sample_price.json`. | JSON |

## How it works

- Every request has a 5-second timeout.
- `live_price.py` logs HTTP 4xx and 5xx responses as `ClientError` and `ServerError` with the status code. Timeouts and connection errors are caught separately, so the log shows where a failure happened. For example, `ReadTimeout` means it connected but the server was slow; `ConnectTimeout` means it couldn't connect at all.
- The FRED scripts print any non-200 status code to stderr and exit with code 1.
- Each run of `live_price.py` writes exactly one line to `tracker.log`, always in the same field order, so the log can be parsed by scripts.

## Setup

Tested on Python 3.14, Ubuntu on WSL.

```bash
git clone https://github.com/finley-matthew/market-tracker.git
cd market-tracker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The FRED scripts need a free API key from [FRED](https://fred.stlouisfed.org/docs/api/api_key.html), stored in a `.env` file in the project folder (already in `.gitignore`):

```
FRED_KEY=your_key_here
```

## Usage

```bash
python3 live_price.py      # prints the price and appends one line to tracker.log
python3 fred_spread.py     # prints "10Y-2Y spread: <value>% (<date>)"
python3 fred_xml.py        # same result, via XML
```

## Log format

```
2026-10-07 10:00:01,366 INFO XAU 4142.3
2026-10-06 10:00:06,021 ERROR Timeout XAU ConnectTimeout
```

| Field | Content |
|---|---|
| 1–2 | Date and time |
| 3 | `INFO` for a successful run, `ERROR` for a failure |
| 4 | On success, the symbol. On failure, the error type (`Timeout`, `ConnectionError`, `ClientError`, `ServerError`, `RequestException`) |
| 5+ | On success, the price. On failure, the symbol and detail (exception class or HTTP status code) |

The tools in [infra-labs](https://github.com/finley-matthew/infra-labs) rely on this layout to count successes, group errors and find missed runs.

## Scheduling

`live_price.py` runs hourly under cron. The entry is in [`crontab.txt`](crontab.txt):

```
0 * * * * cd /path/to/market-tracker && /path/to/market-tracker/.venv/bin/python live_price.py >> cron.log 2>&1
```

The `cd` is there because cron starts jobs in the home folder and the script writes `tracker.log` to the current folder. The venv's Python is called by full path because cron doesn't activate the venv. `2>&1` sends errors such as tracebacks to `cron.log` as well, so a crash leaves evidence.

Since cron runs inside WSL, the job only runs while my PC is on. That caused a six-hour gap on 13 October ([write-up](https://github.com/finley-matthew/infra-labs/blob/main/incidents/2026-10-13-scheduler-host-offline.md)). Moving it to an always-on host is on the roadmap.

## Security

The FRED key lives in `.env`, which is ignored by Git along with the venv and log files. It has never been committed.

While I was building `fred_spread.py`, an unhandled connection error printed the full request URL to my terminal, **including the API key**. Nothing was committed, but since then the error handlers only print the exception's class name, never the exception itself. `fred_xml.py` is the one exception: it prints the full `ParseError`, because the parser only sees the response body, which doesn't contain the key.

## Maintenance

Dependencies are pinned with `==` in `requirements.txt`. In October I patched `charset-normalizer` (a dependency of `requests`) from 3.5.1 to 3.5.2: I saved a `pip freeze` snapshot, installed the exact version, re-ran the scripts, checked the diff, then updated the pin. To roll back, reinstall 3.5.1 and `git restore requirements.txt`.

Python code is checked with `pycodestyle` (line limit 99, set in `setup.cfg`).

## Roadmap

The plan is to grow this from a single price logger into something that collects related data from several sources, stores it, and compares it.

1. Foundations: store readings in SQLite, split the code into one module per source with a `main()` entry point, add `pytest` tests run by GitHub Actions, switch from cron to systemd timers, and retry with backoff after timeouts.
2. More data:

   | Data | Source | Format and update rate | Access |
   |---|---|---|---|
   | Silver (XAG) | Gold API | JSON, on request | No key |
   | Brent crude oil (`DCOILBRENTEU`) | FRED | JSON, daily | API key |
   | US dollar / pound exchange rate | FRED | JSON, daily | API key |
   | 10-year minus 3-month spread (`T10Y3M`) | FRED | JSON, daily | API key |
   | US 10-year real yield (`DFII10`) | FRED | JSON, daily | API key |
   | UK average pump prices | GOV.UK weekly road fuel prices | CSV, weekly | None |
   | Local forecourt fuel prices | GOV.UK Fuel Finder API | JSON, near real time | OAuth 2.0 |
   | UK gilt yields | Bank of England | To be confirmed | To be confirmed |
   | UK inflation (CPI) | ONS | To be confirmed | To be confirmed |

3. Comparisons and charts: Brent crude converted to pence per litre against UK pump prices (how fast do pump prices follow crude, and do they fall as fast as they rise?), Treasury spreads over time with inversions shaded, gold against US real yields, gold in dollars against gold in pounds, the gold/silver ratio, UK gilts against US Treasuries, and a daily summary for each series.
4. Hosting: a small JSON API for the stored data, a Docker image, and an always-on AWS EC2 instance built with Terraform, with CloudWatch alarms and backups to S3.

I'll check each new source's terms of use before building on it.

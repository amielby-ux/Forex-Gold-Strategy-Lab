# Dukascopy connectivity incident

On 2026-10-09 GitHub Actions run 37922758963 failed its real XAUUSD
hourly archive download with HTTP 503 Service Unavailable.

Python unit tests passed independently. The 503 is a remote HTTP response;
it does not establish whether the cause is a transient outage, unsupported
endpoint, CDN restriction or automated-request filtering.

## Next steps
1. Check provider documentation and terms for permitted automated historical downloads.
2. Confirm the archive endpoint and symbol naming with a small, read-only request.
3. If permitted, retry with conservative rate limiting and a clearly identified
   user agent. Do not rotate identities or evade access restrictions.
4. If the provider does not permit or reliably serve automated requests, obtain
   a licensed CSV export from Dukascopy or a broker and import it with
   `strategy_lab.data.load_ohlc_csv`.
5. Do not run performance comparisons until a live sample has passed quote,
   timestamp, spread and completeness checks.

No historical XAUUSD prices or real strategy performance metrics have yet been verified.

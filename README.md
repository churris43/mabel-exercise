# mabel

## Build and run the container

```bash
docker compose up --build
```

## Run the test suite

```bash
docker compose run --rm app pytest
```

## Process the transactions provided in the specs folder

```bash
docker compose run --rm app python main.py
```

This reads the account balances and transactions from the `specs` folder, applies
every transfer, and writes two timestamped CSV files to `storage/reports`:

- `account_balance_*` — the updated balance for each account after all transfers
  have been applied.
- `transfer_report_*` — one row per transfer with its outcome (success or
  failure), so you can see exactly what happened to each one.

The original `specs` files are left untouched; each run produces a fresh pair of
reports.

## Stop the container

```bash
docker compose down
```

## Assumptions

- Monetary amounts are kept to 2 decimal places (cents), rounding half-up.
- A batch keeps going when a transfer fails: the failed one is recorded and the rest are still processed.
- Loading the account balances and transactions files fails fast on a bad format or an unknown account, rather than processing partial data.

## Nice-to-have improvements

- Fire an event when a transfer is processed, so other parts of the system can react to the change.
- Keep a log of failed transfers so they can be retried later.
- Include a transferId on the mable_transactions.csv file to better identify source and results
- Process transfers as a stream/iterator to be able to cope with a much larger transaction set

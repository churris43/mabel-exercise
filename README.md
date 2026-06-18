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

_Note:_ The main.py will generate 2 reports in storage/reports

account_balance\* : Contains the new account balances after processing the mable_transactions.csv file

transfer_report\* : Contains the results of the transfers included in mable_transactions.csv

## Stop the container

```bash
docker compose down
```

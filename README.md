# mabel

## Usage:

# Build and run the container

docker compose up --build

# Run the test suite

docker compose run --rm app pytest — run the test suite

# Process the transactions provided in the specs folder

docker compose run --rm app python main.py

Note: The main.py will generate 2 reports in storage/reports
account*balance*_ : Contains the new account balances after processing the mable*transactions.csv file
transfer_report*_ : Contains the results of the transfers included in mable_transactions.csv

# Stop the container

docker compose down

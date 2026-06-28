import sys
from pathlib import Path

# src/ holds the package root; put it on the path so `domains...` imports resolve.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from domains.transfers.application.process_transfers import ProcessTransfers

if __name__ == "__main__":
    source_account_balances_file_path = "specs/mable_account_balances.csv"
    source_transfers_file_path = "specs/mable_transactions.csv"
    reports_file_path = "storage/reports/"
    print(f"Processing transfers:")
    print(f"-->Source balance files {source_account_balances_file_path}")
    print(f"-->Source Transfer file: {source_transfers_file_path}")
    print("--------------")
    result = ProcessTransfers(
        source_account_balances_file_path,
        source_transfers_file_path,
        reports_file_path
    ).run()

    print(f"Updated balances written to {result.balances_path}")
    print(f"Transfer report written to {result.report_path}")

import sys
from pathlib import Path

# src/ holds the package root; put it on the path so `contexts...` imports resolve.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from contexts.transfers.application.process_transfers import ProcessTransfers
from contexts.transfers.infrastructure.csv_account_repository import CsvAccountRepository
from contexts.transfers.infrastructure.csv_account_reporter import CsvAccountReporter
from contexts.transfers.infrastructure.csv_transfer_loader import CsvTransferLoader
from contexts.transfers.infrastructure.csv_transfer_reporter import CsvTransferReporter
from contexts.transfers.infrastructure.json_account_reporter import JsonAccountReporter
from contexts.transfers.infrastructure.json_transfer_reporter import JsonTransferReporter


if __name__ == "__main__":
    source_account_balances_file_path = "specs/mable_account_balances.csv"
    source_transfers_file_path = "specs/mable_transactions.csv"
    reports_file_path = "storage/reports/"
    print(f"Processing transfers:")
    print(f"-->Source balance files {source_account_balances_file_path}")
    print(f"-->Source Transfer file: {source_transfers_file_path}")
    print("--Example #1 Exporting to CSV format --")
    result = ProcessTransfers(
        CsvAccountRepository(source_account_balances_file_path),
        CsvTransferLoader(source_transfers_file_path),
        CsvTransferReporter(reports_file_path),
        CsvAccountReporter(reports_file_path),
    ).run()
    print(f"Updated balances written to {result.balances_path}")
    print(f"Transfer report written to {result.report_path}")
    
    print("\n\n\n")
    print("--Example #2 Exporting to json format --")
    result = ProcessTransfers(
        CsvAccountRepository(source_account_balances_file_path),
        CsvTransferLoader(source_transfers_file_path),
        JsonTransferReporter(reports_file_path),
        JsonAccountReporter(reports_file_path),
    ).run()
    print(f"Updated balances written to {result.balances_path}")
    print(f"Transfer report written to {result.report_path}")

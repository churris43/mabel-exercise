from dataclasses import dataclass
from pathlib import Path

from domains.transfers.domain.transfer import Transfer
from domains.transfers.domain.transfer_execution import TransferExecution
from domains.transfers.infrastructure.csv_account_reporter import CsvAccountReporter
from domains.transfers.infrastructure.csv_account_repository import CsvAccountRepository
from domains.transfers.infrastructure.csv_transfer_loader import CsvTransferLoader
from domains.transfers.infrastructure.csv_transfer_reporter import CsvTransferReporter


@dataclass
class TransferResult:
    """Outcome of one ProcessTransfers run: the processed transfers and the
    paths of the files written for them."""

    transfers: list[Transfer]
    balances_path: Path | None  # None when there were no accounts to save
    report_path: Path


class ProcessTransfers:
    """One day's run: load balances and transfers from CSV, process them, and
    write the updated balances and a transfer report.

    It owns the I/O (which CSV adapters to use, where output goes); TransferExecution stays
    focused on the pure domain processing.
    """

    def __init__(
        self,
        account_csv_path: str | Path,
        transfers_csv_path: str | Path,
        output_path: str | Path = "storage/reports/",
    ):
        self._account_repo = CsvAccountRepository(account_csv_path)
        self._transfer_loader = CsvTransferLoader(transfers_csv_path)
        self._account_reporter = CsvAccountReporter(output_path)
        self._transfer_reporter = CsvTransferReporter(output_path)

    def run(self) -> TransferResult:
        transfers = self._transfer_loader.load()
        processed_transfers = TransferExecution(self._account_repo).execute_batch(transfers)
        
        # Write the (possibly mutated) balances snapshot. No accounts loaded means
        # nothing was touched, so there is nothing to write (balances_path stays None).
        updated_accounts = self._account_repo.loaded_accounts()
        
        balances_report_path = self._account_reporter.write(updated_accounts) if updated_accounts else None

        transfer_report_path = self._transfer_reporter.write(processed_transfers)
        return TransferResult(processed_transfers, balances_report_path, transfer_report_path)

from __future__ import annotations  # required for `X | None` type hints on Python < 3.10

from dataclasses import dataclass
from pathlib import Path

from contexts.transfers.domain.transfer import Transfer
from contexts.transfers.domain.transfer_execution import TransferExecution
from contexts.transfers.domain.repositories import AccountRepository
from contexts.transfers.infrastructure.csv_transfer_loader import CsvTransferLoader
from contexts.transfers.application.reporter import AccountReporter, TransferReporter


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

    It orchestrates the I/O via injected ports (the transfer and account reporters,
    plus the repository and loader); TransferExecution stays focused on the pure
    domain processing.
    """

    def __init__(
        self,
        account_repository: AccountRepository,
        transfer_loader: CsvTransferLoader,
        transfer_reporter: TransferReporter,
        account_reporter: AccountReporter,
    ):
        self._account_repo = account_repository
        self._transfer_loader = transfer_loader
        self._account_reporter = account_reporter
        self._transfer_reporter = transfer_reporter

    def run(self) -> TransferResult:
        transfers = self._transfer_loader.load()
        processed_transfers = TransferExecution(self._account_repo).execute_batch(transfers)
        
        # Write the (possibly mutated) balances snapshot. No accounts loaded means
        # nothing was touched, so there is nothing to write (balances_path stays None).
        updated_accounts = self._account_repo.loaded_accounts()
        
        balances_report_path = self._account_reporter.write(updated_accounts) if updated_accounts else None

        transfer_report_path = self._transfer_reporter.write(processed_transfers)
        return TransferResult(processed_transfers, balances_report_path, transfer_report_path)

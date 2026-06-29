from contexts.transfers.domain.exceptions import TransferError
from contexts.transfers.domain.repositories import AccountRepository
from contexts.transfers.domain.transfer import Transfer


class TransferExecution:
    """Domain service: applies fund transfers between accounts.

    It coordinates two Accounts (debit the source, credit the destination) and
    records the outcome on the Transfer. It depends only on the
    AccountRepository interface, so all I/O and persistence stay in the application
    and infrastructure layers.

    """

    def __init__(self, repository: AccountRepository):
        self.repository = repository

    def execute(self, transfer: Transfer):
        try:
            from_account = self.repository.get_by_number(transfer.from_account_number)
            to_account = self.repository.get_by_number(transfer.to_account_number)
            # A transfer must be all-or-nothing across the two Account aggregates.
            # Each balance change still goes through its own root (debit/credit);
            # if the credit fails after the debit succeeded, we compensate by
            # crediting the source back, so neither balance is left half-updated.
            from_account.debit(transfer.amount)
            try:
                to_account.credit(transfer.amount)
            except Exception:
                from_account.credit(transfer.amount)
                raise
            transfer.mark_successful()
        except TransferError as error:
            transfer.mark_failed(str(error))

        return transfer

    def execute_batch(self, transfers: list[Transfer]) -> list[Transfer]:
        """ Process a list of transfers and returns the results.
        If a transfer fails due to not having sufficient funds, the transfer
        gets marked as failed and will continue to process the rest of the transfers
        """
        processed_transfers: list[Transfer] = []
        for t in transfers:
            self.execute(t)
            processed_transfers.append(t)
        return processed_transfers
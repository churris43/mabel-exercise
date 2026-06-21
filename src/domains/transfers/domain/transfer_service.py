from domains.transfers.domain.exceptions import TransferError
from domains.transfers.domain.repositories import AccountRepository
from domains.transfers.domain.transfer import Transfer


class TransferService:
    """Domain service: applies fund transfers between accounts.

    It coordinates two Accounts (debit the source, credit the destination) and
    records the outcome on the Transfer. It depends only on the
    AccountRepository port/interface, so all I/O and persistence stay in the application
    and infrastructure layers.
    
    """

    def __init__(self, repository: AccountRepository):
        self.repository = repository

    def process(self, transfer: Transfer):
        try:
            from_account = self.repository.get_by_number(transfer.from_account_number)
            to_account = self.repository.get_by_number(transfer.to_account_number)
            # A transfer must be all-or-nothing across the two Account aggregates.
            # Each balance change still goes through its own root (debit/credit);
            # if the credit fails after the debit succeeded, we compensate by
            # crediting the source back, so neither balance is left half-updated.
            # NOTE: we compensate on ANY failure (except Exception) but only mark
            # the transfer FAILED for domain-rule violations (except TransferError).
            # An unexpected error (a bug, infra failure) is still rolled back, then
            # propagates so it surfaces loudly rather than masquerading as a normal
            # failed transfer.
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

    def process_batch(self, transfers: list[Transfer]) -> list[Transfer]:
        """ Process a list of transfers and returns the results.
        If a transfer fails due to not having sufficient funds, the transfer
        gets marked as failed and will continue to process the rest of the transfers
        """
        transfer_results: list[Transfer] = []
        for t in transfers:
            self.process(t)
            transfer_results.append(t)
        return transfer_results

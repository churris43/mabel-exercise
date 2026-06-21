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
            # NOTE: debit and credit are two separate steps with no rollback. Today this is
            # safe because the only failure is insufficient funds, which is raised by debit
            # before any balance changes (credit never runs). If a failure could ever occur
            # between these two lines (e.g. credit raising), from_account would be left
            # debited without a matching credit. Add a rollback/guard if that becomes possible.
            from_account.debit(transfer.amount)
            to_account.credit(transfer.amount)
            transfer.mark_successful()
        except Exception as error:
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

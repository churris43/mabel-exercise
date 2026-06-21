from domains.transfers.domain.account_number import AccountNumber
from domains.transfers.domain.money import Money

class Account:
    """Entity identified by its AccountNumber, holding a mutable Money balance.

    Behaviour rules:
    - debit(amount) lowers the balance; it cannot go negative — a debit larger
      than the current balance raises InsufficientFundsError (via Money) and
      leaves the balance unchanged;
    - credit(amount) raises the balance;
    - the balance is always a valid Money (non-negative, whole-cent).
    """

    def __init__(self, number: AccountNumber, balance: Money):
        self.number = number
        self.balance = balance
    
    def debit(self, amount: Money):
        self.balance = self.balance.subtract(amount)
        
    def credit(self, amount: Money):
        self.balance = self.balance.add(amount)
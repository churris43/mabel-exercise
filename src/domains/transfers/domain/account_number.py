from dataclasses import dataclass

from domains.transfers.domain.exceptions import InvalidAccountNumberError

@dataclass(frozen=True)
class AccountNumber:
    """Value object for a bank account number.

    Validity rules (enforced on construction):
    - must be all digits (no spaces, signs, or separators);
    - must be exactly 16 digits long.

    Any value breaking these rules raises InvalidAccountNumberError.
    """

    value: str

    def __post_init__(self):
        if not self.value.isdigit() or len(self.value) != 16:
            raise InvalidAccountNumberError
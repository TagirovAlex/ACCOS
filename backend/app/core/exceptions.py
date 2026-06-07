class ACCOSException(Exception):
    pass


class InsufficientBalanceError(ACCOSException):
    def __init__(self, balance: float, required: float):
        self.balance = balance
        self.required = required
        super().__init__(f"Insufficient balance: {balance} < {required}")


class AuthenticationError(ACCOSException):
    pass


class NotFoundError(ACCOSException):
    pass


class AdapterError(ACCOSException):
    pass

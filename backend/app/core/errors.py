class ServiceError(Exception):
    def __init__(self, code: str, message: str, status: int = 422, *, diagnostic: dict | None = None):
        self.code, self.message, self.status = code, message, status
        self.diagnostic = diagnostic
        super().__init__(message)

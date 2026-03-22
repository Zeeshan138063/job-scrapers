class InvalidCredentialsError(Exception):
    """Raised when the login credentials are explicitly rejected by the server."""
    pass


class AccountBlockedError(Exception):
    """Raised when the account is blocked or suspended."""
    pass


class AuthServiceError(Exception):
    """Raised when the authentication service is unreachable or rate-limited."""
    pass

class AIAppError(Exception):
    """
    Base exception for HomeGrownAI. You should never need to use this exception directly, rather, you should use one of the exceptions below.

    If an appropriate exception does *not* already exist, you may define one, but it must either inherit from this class OR have a good
    reason for inheriting from a subclass (e.g., you want to be more specific about the TYPE of DatabaseError you get, so you implement
                                           a DatabaseReadError for when SELECT returns an error).
    """

    def __init__(self, message):
        super().__init__(message)


class InsufficientPermissions(AIAppError):
    def __init__(self):
        super().__init__("Insufficient Permissions.")


class DatabaseError(AIAppError):
    def __init__(self):
        super().__init__("Error when attempting to read or write to the database.")


class UserRegistrationError(AIAppError):
    def __init__(self):
        super().__init__("Error when attempting to register a new user.")


class UserNotFoundError(AIAppError):
    def __init__(self):
        super().__init__(
            "Error when attempting to locate a user when no such user exists."
        )


class EmailAlreadyRegisteredError(UserRegistrationError):
    pass


class UserDeletionError(UserNotFoundError):
    pass

class AIAppError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.status_code = status_code


class InsufficientPermissions(AIAppError):
    def __init__(self):
        super().__init__("Insufficient Permissions. Please contact your administrator if you believe this to be an error.", 20)

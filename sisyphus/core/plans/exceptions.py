class PlanError(Exception):
    """Base exception for plan-related errors"""

    pass


class UnsupportedPlanVersionError(PlanError):
    """Raised when plan version is not supported"""

    pass


class PlanValidationError(PlanError):
    """Raised when plan fails validation"""

    pass

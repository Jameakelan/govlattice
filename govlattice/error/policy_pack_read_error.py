class PolicyPackReadError(Exception):
    """Base exception for failures while reading a policy pack."""


class PolicyPackFileError(PolicyPackReadError):
    """Raised when a pack file cannot be accessed safely."""


class PolicyPackValidationError(PolicyPackReadError):
    """Raised when a pack manifest violates its schema."""


class PolicyPackConsistencyError(PolicyPackReadError):
    """Raised when a manifest and its policy files disagree."""


class UnsupportedPolicyPackSchemaError(PolicyPackReadError):
    """Raised when a pack uses an unsupported schema version."""

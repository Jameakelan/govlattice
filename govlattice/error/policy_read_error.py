class PolicyReadError(Exception):
    """Base exception for failures while reading a policy."""


class PolicyFileError(PolicyReadError):
    """Raised when a policy file cannot be accessed safely."""


class PolicySyntaxError(PolicyReadError):
    """Raised when policy YAML cannot be parsed safely."""


class PolicyValidationError(PolicyReadError):
    """Raised when a parsed policy violates its schema."""


class UnsupportedPolicySchemaError(PolicyReadError):
    """Raised when a policy uses an unsupported schema version."""

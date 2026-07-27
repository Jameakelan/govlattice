class GovLatticeEngineError(Exception):
    """Base exception for engine configuration and usage errors."""


class UnknownPolicyStateError(GovLatticeEngineError):
    """Raised when an evaluation targets a state that does not exist."""

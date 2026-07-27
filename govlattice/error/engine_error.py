from govlattice.model import PolicyEvaluationResult


class GovLatticeEngineError(Exception):
    """Base exception for engine configuration and usage errors."""


class UnknownPolicyStateError(GovLatticeEngineError):
    """Raised when an evaluation targets a state that does not exist."""


class PolicyEnforcementError(GovLatticeEngineError):
    """Raised when policy enforcement blocks further execution."""

    __slots__ = ("result",)

    def __init__(self, result: PolicyEvaluationResult) -> None:
        if not isinstance(result, PolicyEvaluationResult):
            raise TypeError(
                "result must be a PolicyEvaluationResult"
            )
        self.result = result
        super().__init__(
            f'policy "{result.policy_id}" enforcement failed '
            f'for state "{result.state_id}" '
            f"with status {result.status.value}"
        )

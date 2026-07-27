from govlattice.nodes.policy_pack_node import PolicyPackNode
from govlattice.verifier.pack_verifier import PackVerifier


class DuplicatePolicyIdError(ValueError):
    pass


class UniquePolicyIdsVerifier(PackVerifier):
    __slots__ = ()

    def verify(self, pack: PolicyPackNode) -> None:
        seen: set[str] = set()
        for entry in pack.policies:
            policy_id = entry.policy.policy_name
            if policy_id in seen:
                raise DuplicatePolicyIdError(
                    f'duplicate policy id "{policy_id}" '
                    f'in pack "{pack.id}"'
                )
            seen.add(policy_id)

from govlattice import __schema_version__
from govlattice.nodes.policy_pack_node import PolicyPackNode
from govlattice.verifier.pack_verifier import PackVerifier


class PolicySchemaVersionVerifier(PackVerifier):
    __slots__ = ()

    def verify(self, pack: PolicyPackNode) -> None:
        if not __schema_version__:
            raise ValueError(
                f'pack "{pack.id}" has no policy schema version'
            )

from urllib.parse import urlsplit

from govlattice.nodes.policy_pack_node import PolicyPackNode
from govlattice.verifier.pack_verifier import PackVerifier


class PolicyReferencesVerifier(PackVerifier):
    __slots__ = ()

    def verify(self, pack: PolicyPackNode) -> None:
        for entry in pack.policies:
            for reference in entry.policy.references:
                parsed = urlsplit(reference.url)
                if (
                    parsed.scheme not in {"http", "https"}
                    or not parsed.netloc
                ):
                    raise ValueError(
                        f'policy "{entry.policy.policy_name}" '
                        f'has an invalid reference URL "{reference.url}"'
                    )

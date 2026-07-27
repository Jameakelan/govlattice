from pathlib import Path
import re
from typing import Any
from typing import Optional
from typing import Sequence
from typing import Union

from govlattice.builder.pack_yaml_builder import PackYamlBuilder
from govlattice.designer.policy_designer import PolicyDesigner
from govlattice.nodes.policy_pack_entry_node import PolicyPackEntryNode
from govlattice.nodes.policy_pack_node import PolicyPackNode
from govlattice.utils.helper.file_helper import resolve_output_directory
from govlattice.verifier.policy_references_verifier import (
    PolicyReferencesVerifier,
)
from govlattice.verifier.policy_schema_version_verifier import (
    PolicySchemaVersionVerifier,
)
from govlattice.verifier.unique_policy_ids_verifier import (
    UniquePolicyIdsVerifier,
)


class PolicyPackDesigner:
    __slots__ = ("_pack",)

    def __init__(
        self,
        pack_id: str,
        name: str,
        version: str,
        *,
        purpose: Optional[str] = None,
        enabled: bool = True,
        jurisdiction: Sequence[str] = (),
        tags: Sequence[str] = (),
        **metadata: Any,
    ) -> None:
        self._pack = PolicyPackNode(
            pack_id=pack_id,
            name=name,
            version=version,
            purpose=purpose,
            enabled=enabled,
            jurisdiction=jurisdiction,
            tags=tags,
            metadata=metadata,
        )

    @property
    def purpose(self) -> Optional[str]:
        return self._pack.purpose

    def add_policy(
        self,
        policy: PolicyDesigner,
    ) -> "PolicyPackDesigner":
        if not isinstance(policy, PolicyDesigner):
            raise TypeError("policy must be a PolicyDesigner")
        if not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9._-]*",
            policy.policy_name,
        ):
            raise ValueError(
                "policy name must be file-safe when added to a pack"
            )

        self._pack.policies.append(
            PolicyPackEntryNode(
                policy=policy,
                file_name=f"{policy.policy_name}.yml",
            )
        )
        return self

    def verify_unique_policy_ids(self) -> "PolicyPackDesigner":
        UniquePolicyIdsVerifier().verify(self._pack)
        return self

    def verify_schema_versions(self) -> "PolicyPackDesigner":
        PolicySchemaVersionVerifier().verify(self._pack)
        return self

    def verify_policy_references(self) -> "PolicyPackDesigner":
        PolicyReferencesVerifier().verify(self._pack)
        return self

    def execute(
        self,
        name: str,
        output_dir: Union[str, Path] = "policies",
    ) -> Path:
        directory_name = PolicyPackNode._validate_id(name)
        self.verify_unique_policy_ids()
        self.verify_schema_versions()
        self.verify_policy_references()

        root = resolve_output_directory(output_dir)
        pack_directory = root / directory_name
        policy_directory = pack_directory / "policies"
        policy_directory.mkdir(parents=True, exist_ok=True)

        for entry in self._pack.policies:
            entry.policy.execute(
                entry.file_name,
                output_dir=policy_directory,
            )

        return PackYamlBuilder(self._pack).write(pack_directory)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from govlattice.designer.policy_designer import PolicyDesigner


class PolicyPackEntryNode:
    __slots__ = ("policy", "file_name")

    def __init__(
        self,
        policy: "PolicyDesigner",
        file_name: str,
    ) -> None:
        self.policy = policy
        self.file_name = file_name

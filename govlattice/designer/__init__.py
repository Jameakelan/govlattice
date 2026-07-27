from abc import ABC
from abc import abstractmethod
from pathlib import Path
from typing import Union

from govlattice.builder.expectation_builder import ExpectationBuilder


class Designer(ABC):
    __slots__ = ("_policy_name",)

    def __init__(self, policy_name: str) -> None:
        if not isinstance(policy_name, str):
            raise TypeError("policy_name must be a string")

        policy_name = policy_name.strip()
        if not policy_name:
            raise ValueError("policy_name must not be empty")

        self._policy_name = policy_name

    @property
    def policy_name(self) -> str:
        return self._policy_name

    @abstractmethod
    def state(self, id: str) -> ExpectationBuilder:
        pass

    @abstractmethod
    def execute(
        self,
        name: str,
        output_dir: Union[str, Path] = "policies",
    ) -> Path:
        pass

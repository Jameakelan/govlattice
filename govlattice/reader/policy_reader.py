from govlattice.model import PolicyDefinition
from govlattice.reader.policy_definition_factory import (
    PolicyDefinitionFactory,
)
from govlattice.reader.policy_yaml_loader import MAX_POLICY_FILE_BYTES
from govlattice.reader.policy_yaml_loader import PathInput
from govlattice.reader.policy_yaml_loader import PolicyYamlLoader
from govlattice.validator import PolicyValidator


class PolicyReader:
    MAX_FILE_BYTES = MAX_POLICY_FILE_BYTES

    @classmethod
    def read(cls, path: PathInput) -> PolicyDefinition:
        document = PolicyYamlLoader.load(path)
        PolicyValidator.validate(document)
        return PolicyDefinitionFactory.create(document)

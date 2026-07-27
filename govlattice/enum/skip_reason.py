from enum import Enum


class SkipReason(str, Enum):
    POLICY_DISABLED = "policy_disabled"
    SEGMENT_EMPTY = "segment_empty"
    NOT_APPLICABLE = "not_applicable"
    ACTOR_NOT_PROVIDED = "actor_not_provided"

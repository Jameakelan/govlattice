from enum import Enum


class ActorType(str, Enum):
    HUMAN = "human"
    SERVICE = "service"
    WORKFLOW = "workflow"

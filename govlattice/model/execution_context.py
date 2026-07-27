from dataclasses import dataclass
from typing import Any
from typing import Mapping
from typing import Optional

from govlattice.enum import ActorType
from govlattice.model.immutable import freeze_value


@dataclass(frozen=True, init=False)
class ActorProfile:
    __slots__ = (
        "subject_id",
        "actor_type",
        "display_name",
        "email",
        "team",
        "roles",
        "metadata",
    )

    subject_id: str
    actor_type: ActorType
    display_name: Optional[str]
    email: Optional[str]
    team: Optional[str]
    roles: tuple[str, ...]
    metadata: Mapping[str, Any]

    def __init__(
        self,
        subject_id: str,
        *,
        actor_type: ActorType = ActorType.HUMAN,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        team: Optional[str] = None,
        roles: tuple[str, ...] = (),
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> None:
        if not isinstance(subject_id, str) or not subject_id.strip():
            raise ValueError("subject_id must be a non-empty string")
        if not isinstance(actor_type, ActorType):
            raise TypeError("actor_type must be an ActorType")
        if not isinstance(roles, tuple):
            raise TypeError("roles must be a tuple of strings")
        normalized_roles: list[str] = []
        for role in roles:
            if not isinstance(role, str) or not role.strip():
                raise ValueError(
                    "roles must contain non-empty strings"
                )
            role = role.strip()
            if role not in normalized_roles:
                normalized_roles.append(role)

        object.__setattr__(self, "subject_id", subject_id.strip())
        object.__setattr__(self, "actor_type", actor_type)
        object.__setattr__(
            self,
            "display_name",
            self._optional_text("display_name", display_name),
        )
        object.__setattr__(
            self,
            "email",
            self._optional_text("email", email),
        )
        object.__setattr__(
            self,
            "team",
            self._optional_text("team", team),
        )
        object.__setattr__(self, "roles", tuple(normalized_roles))
        object.__setattr__(
            self,
            "metadata",
            freeze_value(dict(metadata or {})),
        )

    @staticmethod
    def _optional_text(
        name: str,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")
        return value.strip()


@dataclass(frozen=True, init=False)
class ExecutionContext:
    __slots__ = (
        "actor",
        "environment",
        "run_id",
        "source",
        "metadata",
    )

    actor: Optional[ActorProfile]
    environment: Optional[str]
    run_id: Optional[str]
    source: Optional[str]
    metadata: Mapping[str, Any]

    def __init__(
        self,
        *,
        actor: Optional[ActorProfile] = None,
        environment: Optional[str] = None,
        run_id: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> None:
        if actor is not None and not isinstance(actor, ActorProfile):
            raise TypeError("actor must be an ActorProfile")
        object.__setattr__(self, "actor", actor)
        object.__setattr__(
            self,
            "environment",
            ActorProfile._optional_text(
                "environment",
                environment,
            ),
        )
        object.__setattr__(
            self,
            "run_id",
            ActorProfile._optional_text("run_id", run_id),
        )
        object.__setattr__(
            self,
            "source",
            ActorProfile._optional_text("source", source),
        )
        object.__setattr__(
            self,
            "metadata",
            freeze_value(dict(metadata or {})),
        )

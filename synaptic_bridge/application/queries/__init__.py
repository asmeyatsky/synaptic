"""
Application Queries

Query handlers following CQRS pattern.
Each query is a separate class with a single responsibility.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class GetSessionQuery:
    session_id: str

    async def execute(self, session_repo: Any) -> Any:
        return await session_repo.get_by_id(self.session_id)


@dataclass
class ListSessionsQuery:
    user_id: str

    async def execute(self, session_repo: Any) -> list[Any]:
        return await session_repo.get_by_user(self.user_id)


@dataclass
class GetCognitiveStateQuery:
    state_id: str

    async def execute(self, classifier_port: Any) -> Any:
        pass


@dataclass
class ListCognitiveStatesQuery:
    session_id: str

    async def execute(self, classifier_port: Any) -> list[Any]:
        pass


@dataclass
class GetDeviceQuery:
    device_id: str

    async def execute(self, device_port: Any) -> Any:
        pass


@dataclass
class ListDevicesQuery:
    user_id: str

    async def execute(self, device_port: Any) -> list[Any]:
        pass


@dataclass
class GetUserQuery:
    user_id: str

    async def execute(self, user_repo: Any) -> Any:
        return await user_repo.get_by_id(self.user_id)

from collections import deque
from dataclasses import dataclass
from threading import Lock
from typing import Literal
from uuid import UUID, uuid4


MAX_HISTORY_MESSAGES = 10


@dataclass(frozen=True)
class ConversationMessage:
    role: Literal["user", "assistant"]
    content: str


class ConversationNotFoundError(Exception):
    pass


class ConversationStore:
    """Temporary, process-local storage for recent conversation messages."""

    def __init__(self, max_messages: int = MAX_HISTORY_MESSAGES):
        self.max_messages = max_messages
        self._conversations: dict[UUID, deque[ConversationMessage]] = {}
        self._lock = Lock()

    def create(self) -> UUID:
        with self._lock:
            conversation_id = uuid4()
            self._conversations[conversation_id] = deque(maxlen=self.max_messages)
        return conversation_id

    def get_recent(self, conversation_id: UUID) -> list[ConversationMessage]:
        with self._lock:
            messages = self._conversations.get(conversation_id)
            if messages is None:
                raise ConversationNotFoundError
            return list(messages)

    def append_exchange(
        self,
        conversation_id: UUID,
        user_message: str,
        assistant_message: str,
    ) -> None:
        with self._lock:
            messages = self._conversations.get(conversation_id)
            if messages is None:
                raise ConversationNotFoundError
            messages.append(ConversationMessage(role="user", content=user_message))
            messages.append(
                ConversationMessage(role="assistant", content=assistant_message)
            )

    def clear(self) -> None:
        with self._lock:
            self._conversations.clear()

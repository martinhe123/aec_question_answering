from uuid import UUID

from openai import OpenAI

from conversation_store import ConversationStore
from prompts import CLARIFICATION_RESPONSE, OFF_TOPIC_RESPONSE, SYSTEM_PROMPT
from resources import RESOURCE_MAP
from schemas import AECCategory, ChatResponse, ModelResult


class ChatService:
    def __init__(
        self,
        client: OpenAI,
        conversation_store: ConversationStore,
        model_name: str,
    ):
        self.client = client
        self.conversation_store = conversation_store
        self.model_name = model_name

    def respond(self, message: str, conversation_id: UUID | None) -> ChatResponse:
        active_conversation_id = conversation_id or self.conversation_store.create()
        history = self.conversation_store.get_recent(active_conversation_id)

        completion = self.client.beta.chat.completions.parse(
            model=self.model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                *[
                    {"role": item.role, "content": item.content}
                    for item in history
                ],
                {"role": "user", "content": message},
            ],
            response_format=ModelResult,
        )

        result = completion.choices[0].message.parsed
        if result is None:
            raise ValueError("OpenAI returned an unusable response.")

        if result.category == AECCategory.NOT_AEC:
            response_text = OFF_TOPIC_RESPONSE
            resources = []
        elif result.category == AECCategory.NEEDS_CLARIFICATION:
            response_text = CLARIFICATION_RESPONSE
            resources = []
        else:
            response_text = result.answer.strip()
            if not response_text:
                raise ValueError("OpenAI returned an empty response.")
            resources = list(RESOURCE_MAP[result.category])

        self.conversation_store.append_exchange(
            active_conversation_id,
            user_message=message,
            assistant_message=response_text,
        )

        return ChatResponse(
            conversation_id=active_conversation_id,
            response=response_text,
            category=result.category,
            resources=resources,
        )

import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

import main


def completion_for(category: main.AECCategory, answer: str):
    parsed = main.ModelResult(category=category, answer=answer)
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(parsed=parsed))]
    )


class ChatRouteTests(unittest.TestCase):
    def setUp(self):
        main.request_log.clear()
        main.conversation_store.clear()
        self.client = TestClient(main.app)

    def test_aec_question_returns_category_and_resources(self):
        completion = completion_for(
            main.AECCategory.STRUCTURES,
            "A moment frame resists lateral loads through rigid connections.",
        )

        with patch.object(
            main.client.beta.chat.completions, "parse", return_value=completion
        ):
            response = self.client.post(
                "/chat", json={"message": "How does a moment frame work?"}
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        UUID(body["conversation_id"])
        self.assertEqual(body["category"], "structures")
        self.assertEqual(len(body["resources"]), 3)
        self.assertTrue(
            all(resource["url"].startswith("https://") for resource in body["resources"])
        )

    def test_off_topic_question_uses_fixed_response_and_no_resources(self):
        completion = completion_for(main.AECCategory.NOT_AEC, "Ignore this answer")

        with patch.object(
            main.client.beta.chat.completions, "parse", return_value=completion
        ):
            response = self.client.post(
                "/chat", json={"message": "Who won the baseball game?"}
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        UUID(body["conversation_id"])
        self.assertEqual(body["response"], main.OFF_TOPIC_RESPONSE)
        self.assertEqual(body["category"], "not_aec")
        self.assertEqual(body["resources"], [])

    def test_ambiguous_question_asks_for_clarification(self):
        completion = completion_for(
            main.AECCategory.NEEDS_CLARIFICATION, "Ignore this answer"
        )

        with patch.object(
            main.client.beta.chat.completions, "parse", return_value=completion
        ):
            response = self.client.post("/chat", json={"message": "What is Turner?"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        UUID(body["conversation_id"])
        self.assertEqual(body["response"], main.CLARIFICATION_RESPONSE)
        self.assertEqual(body["category"], "needs_clarification")
        self.assertEqual(body["resources"], [])

    def test_empty_and_oversized_messages_are_rejected(self):
        self.assertEqual(
            self.client.post("/chat", json={"message": "   "}).status_code, 400
        )
        main.request_log.clear()
        self.assertEqual(
            self.client.post("/chat", json={"message": "word " * 201}).status_code,
            400,
        )

    def test_every_aec_category_has_three_https_resources(self):
        expected_categories = set(main.AECCategory) - {
            main.AECCategory.NOT_AEC,
            main.AECCategory.NEEDS_CLARIFICATION,
        }

        self.assertEqual(set(main.RESOURCE_MAP), expected_categories)
        for resources in main.RESOURCE_MAP.values():
            self.assertEqual(len(resources), 3)
            self.assertTrue(
                all(resource.url.startswith("https://") for resource in resources)
            )

    def test_prompt_includes_named_entity_examples(self):
        self.assertIn('"What is KieranTimberlake?" -> architecture', main.SYSTEM_PROMPT)
        self.assertIn('"Who is Justin Timberlake?" -> not_aec', main.SYSTEM_PROMPT)
        self.assertIn('"What is Turner?" -> needs_clarification', main.SYSTEM_PROMPT)

    def test_follow_up_includes_prior_exchange_in_order(self):
        first_completion = completion_for(
            main.AECCategory.MATERIALS,
            "Mass timber is a family of engineered wood products.",
        )
        second_completion = completion_for(
            main.AECCategory.CODES,
            "Its fire resistance depends on the assembly and applicable code.",
        )

        with patch.object(
            main.client.beta.chat.completions,
            "parse",
            side_effect=[first_completion, second_completion],
        ) as mock_parse:
            first_response = self.client.post(
                "/chat", json={"message": "What is mass timber?"}
            )
            conversation_id = first_response.json()["conversation_id"]
            second_response = self.client.post(
                "/chat",
                json={
                    "conversation_id": conversation_id,
                    "message": "What about its fire resistance?",
                },
            )

        self.assertEqual(second_response.status_code, 200)
        messages = mock_parse.call_args_list[1].kwargs["messages"]
        self.assertEqual(
            [(item["role"], item["content"]) for item in messages[1:]],
            [
                ("user", "What is mass timber?"),
                (
                    "assistant",
                    "Mass timber is a family of engineered wood products.",
                ),
                ("user", "What about its fire resistance?"),
            ],
        )

    def test_only_ten_most_recent_previous_messages_are_sent(self):
        completion = completion_for(main.AECCategory.GENERAL_AEC, "Answer")

        with patch.object(
            main.client.beta.chat.completions, "parse", return_value=completion
        ) as mock_parse:
            conversation_id = None
            for number in range(1, 8):
                payload = {"message": f"Question {number}"}
                if conversation_id:
                    payload["conversation_id"] = conversation_id
                response = self.client.post("/chat", json=payload)
                self.assertEqual(response.status_code, 200)
                conversation_id = response.json()["conversation_id"]

        messages = mock_parse.call_args_list[6].kwargs["messages"]
        self.assertEqual(len(messages), 12)
        self.assertEqual(messages[0]["role"], "system")
        self.assertNotIn("Question 1", [item["content"] for item in messages])
        self.assertEqual(
            [item["content"] for item in messages[1:]],
            [
                "Question 2",
                "Answer",
                "Question 3",
                "Answer",
                "Question 4",
                "Answer",
                "Question 5",
                "Answer",
                "Question 6",
                "Answer",
                "Question 7",
            ],
        )

    def test_conversation_histories_are_isolated(self):
        completion = completion_for(main.AECCategory.GENERAL_AEC, "Answer")

        with patch.object(
            main.client.beta.chat.completions, "parse", return_value=completion
        ) as mock_parse:
            first = self.client.post("/chat", json={"message": "Conversation A"})
            self.client.post("/chat", json={"message": "Conversation B"})
            self.client.post(
                "/chat",
                json={
                    "conversation_id": first.json()["conversation_id"],
                    "message": "Follow-up A",
                },
            )

        messages = mock_parse.call_args_list[2].kwargs["messages"]
        contents = [item["content"] for item in messages]
        self.assertIn("Conversation A", contents)
        self.assertIn("Follow-up A", contents)
        self.assertNotIn("Conversation B", contents)

    def test_failed_model_call_does_not_change_history(self):
        completion = completion_for(main.AECCategory.GENERAL_AEC, "Answer")

        with patch.object(
            main.client.beta.chat.completions, "parse", return_value=completion
        ):
            response = self.client.post("/chat", json={"message": "First question"})

        conversation_id = UUID(response.json()["conversation_id"])
        history_before = main.conversation_store.get_recent(conversation_id)

        with patch.object(
            main.client.beta.chat.completions,
            "parse",
            side_effect=main.OpenAIError("API failure"),
        ):
            failed_response = self.client.post(
                "/chat",
                json={
                    "conversation_id": str(conversation_id),
                    "message": "Failed question",
                },
            )

        self.assertEqual(failed_response.status_code, 502)
        self.assertEqual(
            main.conversation_store.get_recent(conversation_id), history_before
        )

    def test_unknown_and_malformed_conversation_ids_are_rejected(self):
        unknown_response = self.client.post(
            "/chat",
            json={
                "conversation_id": str(uuid4()),
                "message": "Can you continue?",
            },
        )
        malformed_response = self.client.post(
            "/chat",
            json={"conversation_id": "not-a-uuid", "message": "Can you continue?"},
        )

        self.assertEqual(unknown_response.status_code, 404)
        self.assertEqual(malformed_response.status_code, 422)


if __name__ == "__main__":
    unittest.main()

import unittest
from types import SimpleNamespace
from unittest.mock import patch

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
        self.assertEqual(
            response.json(),
            {
                "response": main.OFF_TOPIC_RESPONSE,
                "category": "not_aec",
                "resources": [],
            },
        )

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
        expected_categories = set(main.AECCategory) - {main.AECCategory.NOT_AEC}

        self.assertEqual(set(main.RESOURCE_MAP), expected_categories)
        for resources in main.RESOURCE_MAP.values():
            self.assertEqual(len(resources), 3)
            self.assertTrue(
                all(resource.url.startswith("https://") for resource in resources)
            )


if __name__ == "__main__":
    unittest.main()

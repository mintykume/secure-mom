import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from pydantic import ValidationError

from backend.llm_extract import _extract_json, extract_decisions
from backend.mom_generator import generate_mom_markdown
from backend.schemas import ActionItem, ExtractionResult


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_transcript.txt"


class ExtractionSchemaTests(unittest.TestCase):
    def test_missing_owner_and_deadline_default_to_null(self):
        extraction = ExtractionResult.model_validate(
            {"meeting_summary": "Review completed.", "action_items": [{"decision": "Review results"}]}
        )

        item = extraction.action_items[0]
        self.assertIsNone(item.owner)
        self.assertIsNone(item.deadline)

    def test_empty_action_items_are_valid(self):
        extraction = ExtractionResult.model_validate(
            {"meeting_summary": "General discussion.", "action_items": []}
        )

        self.assertEqual(extraction.action_items, [])

    def test_missing_extraction_fields_are_invalid(self):
        with self.assertRaises(ValidationError):
            ExtractionResult.model_validate({"meeting_summary": "Incomplete response"})

    def test_confidence_must_be_between_zero_and_one(self):
        with self.assertRaises(ValidationError):
            ActionItem(decision="Review results", confidence=1.2)


class ExtractionParsingTests(unittest.TestCase):
    def test_valid_json_response_is_validated(self):
        payload = {
            "meeting_summary": "The team agreed to prepare a procedure report.",
            "action_items": [
                {
                    "decision": "Prepare the procedure report",
                    "owner": "Dr. Ionescu",
                    "deadline": "by Friday",
                    "evidence": "voi pregăti raportul până vineri",
                    "confidence": 0.95,
                }
            ],
        }
        response = Mock()
        response.json.return_value = {"response": json.dumps(payload)}
        response.raise_for_status.return_value = None

        with patch("backend.llm_extract.requests.post", return_value=response) as post:
            extraction = extract_decisions("Dr. Ionescu va pregăti raportul până vineri.")

        self.assertEqual(extraction["action_items"][0]["owner"], "Dr. Ionescu")
        self.assertEqual(extraction["action_items"][0]["deadline"], "by Friday")
        self.assertEqual(extraction["action_items"][0]["evidence"], "voi pregăti raportul până vineri")
        self.assertEqual(post.call_args.kwargs["json"]["format"], "json")

    def test_extra_prose_around_json_is_accepted(self):
        data = _extract_json(
            'Here is the result:\n```json\n{"meeting_summary":"Done","action_items":[]}\n```'
        )

        self.assertEqual(data, {"meeting_summary": "Done", "action_items": []})

    def test_invalid_json_fails_clearly(self):
        response = Mock()
        response.json.return_value = {"response": "not valid JSON"}
        response.raise_for_status.return_value = None

        with patch("backend.llm_extract.requests.post", return_value=response):
            with self.assertRaisesRegex(ValueError, "valid JSON object"):
                extract_decisions("Some transcript")

    def test_missing_response_text_fails_clearly(self):
        response = Mock()
        response.json.return_value = {}
        response.raise_for_status.return_value = None

        with patch("backend.llm_extract.requests.post", return_value=response):
            with self.assertRaisesRegex(ValueError, "response.*field"):
                extract_decisions("Some transcript")

    def test_invalid_extraction_shape_fails_validation(self):
        response = Mock()
        response.json.return_value = {"response": '{"meeting_summary":"Incomplete response"}'}
        response.raise_for_status.return_value = None

        with patch("backend.llm_extract.requests.post", return_value=response):
            with self.assertRaises(ValidationError):
                extract_decisions("Some transcript")

    def test_unaccepted_suggestion_fixture_is_not_an_action_item(self):
        transcript = FIXTURE_PATH.read_text(encoding="utf-8")
        self.assertIn("Maybe we should review the supply budget", transcript)

        response = Mock()
        response.json.return_value = {
            "response": json.dumps(
                {
                    "meeting_summary": "The team agreed to prepare a procedure report.",
                    "action_items": [
                        {
                            "decision": "Prepare the procedure report",
                            "owner": "Dr. Ionescu",
                            "deadline": "până vineri",
                            "evidence": "voi pregăti raportul până vineri",
                            "confidence": 0.95,
                        }
                    ],
                }
            )
        }
        response.raise_for_status.return_value = None

        with patch("backend.llm_extract.requests.post", return_value=response) as post:
            extraction = extract_decisions(transcript)

        sent_prompt = post.call_args.kwargs["json"]["prompt"]
        self.assertIn("not an action item", sent_prompt)
        self.assertEqual(len(extraction["action_items"]), 1)
        self.assertNotIn("supply budget", extraction["action_items"][0]["decision"])


class MomGeneratorTests(unittest.TestCase):
    def test_mom_renders_items_and_escapes_table_separators(self):
        mom = generate_mom_markdown(
            meeting_type="medical",
            meeting_id="test-123",
            extraction={
                "meeting_summary": "Review completed.",
                "action_items": [
                    {
                        "decision": "Review PCI | stenting",
                        "owner": "Dr. Ionescu",
                        "deadline": None,
                    }
                ],
            },
            detected_language="ro",
            transcript_excerpt="A short multilingual excerpt.",
        )

        self.assertIn("| Review PCI \\| stenting | Dr. Ionescu | — |", mom)
        self.assertIn("Review completed.", mom)
        self.assertIn("A short multilingual excerpt.", mom)

    def test_mom_handles_no_action_items(self):
        mom = generate_mom_markdown(
            meeting_type="administrative",
            meeting_id="test-456",
            extraction={"meeting_summary": "Discussion only.", "action_items": []},
            detected_language=None,
            transcript_excerpt="",
        )

        self.assertIn("_(no action items extracted)_", mom)
        self.assertIn("Detected language: unknown", mom)


if __name__ == "__main__":
    unittest.main()

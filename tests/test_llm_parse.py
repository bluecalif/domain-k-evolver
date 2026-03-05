"""Task 2.2 테스트: LLM 응답 JSON 추출."""

import pytest

from src.utils.llm_parse import extract_json


class TestExtractJson:
    def test_plain_json_object(self):
        result = extract_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_plain_json_array(self):
        result = extract_json('[{"a": 1}, {"b": 2}]')
        assert result == [{"a": 1}, {"b": 2}]

    def test_markdown_fence_json(self):
        text = '```json\n{"target_gaps": ["GU-0001"]}\n```'
        result = extract_json(text)
        assert result == {"target_gaps": ["GU-0001"]}

    def test_markdown_fence_no_lang(self):
        text = '```\n{"key": "val"}\n```'
        result = extract_json(text)
        assert result == {"key": "val"}

    def test_surrounding_text(self):
        text = 'Here is the plan:\n{"plan": true}\nHope this helps!'
        result = extract_json(text)
        assert result == {"plan": True}

    def test_nested_json(self):
        text = '{"queries": {"GU-0001": ["q1", "q2"]}}'
        result = extract_json(text)
        assert result["queries"]["GU-0001"] == ["q1", "q2"]

    def test_array_in_fence(self):
        text = '```json\n[{"claim_id": "CL-01"}]\n```'
        result = extract_json(text)
        assert isinstance(result, list)
        assert result[0]["claim_id"] == "CL-01"

    def test_no_json_raises(self):
        with pytest.raises(ValueError, match="No JSON found"):
            extract_json("No json here at all.")

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match="JSON parse failed"):
            extract_json("{invalid: json}")

    def test_markdown_fence_with_extra_text(self):
        text = "Sure! Here's the result:\n```json\n{\"a\": 1}\n```\nLet me know!"
        result = extract_json(text)
        assert result == {"a": 1}

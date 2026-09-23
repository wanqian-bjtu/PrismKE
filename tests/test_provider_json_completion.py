import json

import pytest

from src.evaluation.request_budget import RequestBudget
from src.providers.common import parse_json_object


@pytest.mark.parametrize("content", ['{"claims":[]}', '```json\n{"claims":[]}\n```'])
def test_plain_or_fenced_json_object_is_parsed_without_paid_repair(content):
    assert parse_json_object(content) == {"claims": []}


@pytest.mark.parametrize("content", ["[]", 'Prose {"claims":[]}', '{"claims":['])
def test_partial_prose_or_non_object_output_is_not_silently_accepted(content):
    with pytest.raises(json.JSONDecodeError):
        parse_json_object(content)


def test_visual_output_allowance_is_included_in_reservation():
    assert RequestBudget().estimate({"messages": [], "max_tokens": 8192}) == 8192 + 1024

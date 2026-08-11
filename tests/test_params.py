"""Parameter-schema contract."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from cad_context import api
from cad_context.generators.models import BracketParams
from cad_context.params import defaults, describe, parse_overrides

REQUIRED_KEYS = {
    "name",
    "type",
    "default",
    "minimum",
    "maximum",
    "step",
    "unit",
    "control",
    "description",
}


def test_schema_lists_every_parameter_with_the_contract_keys():
    schema = describe(BracketParams, generator="bracket-cadquery")
    assert schema["generator"] == "bracket-cadquery"
    names = {p["name"] for p in schema["parameters"]}
    assert names == set(BracketParams.model_fields)
    for parameter in schema["parameters"]:
        assert REQUIRED_KEYS <= set(parameter)
        assert parameter["minimum"] is not None
        assert parameter["maximum"] is not None


def test_every_generator_publishes_a_schema():
    for generator in api.generators():
        schema = api.schema(generator["id"])
        assert schema["parameters"]
        assert schema["formats"]


def test_defaults_match_the_model():
    assert defaults(BracketParams)["width"] == BracketParams().width


def test_parse_overrides_and_coercion():
    assert parse_overrides(["width=90", "hole_diameter=5"]) == {
        "width": "90",
        "hole_diameter": "5",
    }
    assert BracketParams(**parse_overrides(["width=90"])).width == 90.0


def test_out_of_range_and_unknown_parameters_are_rejected():
    with pytest.raises(ValidationError):
        BracketParams(width=1.0)
    with pytest.raises(ValidationError):
        BracketParams(nonsense=1.0)


def test_parse_overrides_requires_key_value():
    with pytest.raises(ValueError, match="key=value"):
        parse_overrides(["width"])

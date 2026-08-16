"""Parameter-schema contract.

A generator declares its parameters as a pydantic model built from
:func:`number` / :func:`integer` / :func:`choice` fields. :func:`describe`
flattens that model into the transport form consumed by any UI (the companion
web app renders controls straight from it) and by agents:

```json
{
  "generator": "bracket-build123d",
  "parameters": [
    {"name": "width", "type": "number", "default": 80.0, "minimum": 20.0,
     "maximum": 300.0, "step": 1.0, "unit": "mm", "description": "..."}
  ]
}
```
"""

from __future__ import annotations

from typing import Any

from annotated_types import Ge, Gt, Le, Lt
from pydantic import BaseModel, ConfigDict, Field


class ShapeParams(BaseModel):
    """Base class for every generator parameter model."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


def number(
    default: float,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
    step: float = 1.0,
    unit: str = "mm",
    description: str = "",
) -> Any:
    return Field(
        default,
        ge=minimum,
        le=maximum,
        description=description,
        json_schema_extra={"step": step, "unit": unit, "control": "slider"},
    )


def integer(
    default: int,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
    step: int = 1,
    unit: str = "",
    description: str = "",
) -> Any:
    return Field(
        default,
        ge=minimum,
        le=maximum,
        description=description,
        json_schema_extra={"step": step, "unit": unit, "control": "slider"},
    )


def choice(default: str, *, options: list[str], description: str = "") -> Any:
    return Field(
        default,
        description=description,
        json_schema_extra={"options": options, "control": "select"},
    )


_TYPES: dict[type, str] = {
    float: "number",
    int: "integer",
    str: "string",
    bool: "boolean",
}


def _bounds(metadata: list[Any]) -> tuple[float | None, float | None]:
    low = high = None
    for item in metadata:
        if isinstance(item, (Ge, Gt)):
            low = item.ge if isinstance(item, Ge) else item.gt
        elif isinstance(item, (Le, Lt)):
            high = item.le if isinstance(item, Le) else item.lt
    return low, high


def describe(model: type[ShapeParams], *, generator: str = "") -> dict[str, Any]:
    """Flatten a parameter model into the transport form."""
    parameters = []
    for name, info in model.model_fields.items():
        extra = dict(info.json_schema_extra or {})
        minimum, maximum = _bounds(list(info.metadata))
        parameters.append(
            {
                "name": name,
                "type": _TYPES.get(info.annotation, "string"),
                "default": info.get_default(),
                "minimum": minimum,
                "maximum": maximum,
                "step": extra.get("step"),
                "unit": extra.get("unit", ""),
                "options": extra.get("options"),
                "control": extra.get("control", "input"),
                "description": info.description or "",
            }
        )
    schema: dict[str, Any] = {"parameters": parameters}
    if generator:
        schema = {"generator": generator, **schema}
    return schema


def defaults(model: type[ShapeParams]) -> dict[str, Any]:
    return {name: info.get_default() for name, info in model.model_fields.items()}


def parse_overrides(pairs: list[str]) -> dict[str, str]:
    """Turn ``["width=90", "holes=3"]`` into a dict; pydantic does the casting."""
    values: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"parameter override must be key=value, got {pair!r}")
        key, _, value = pair.partition("=")
        values[key.strip()] = value.strip()
    return values

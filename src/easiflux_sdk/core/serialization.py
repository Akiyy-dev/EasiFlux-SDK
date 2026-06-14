from __future__ import annotations

import json as json_lib
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlencode


def clean_mapping(mapping: Mapping[str, Any] | None) -> dict[str, Any]:
    if not mapping:
        return {}
    return {key: value for key, value in mapping.items() if value is not None}


def stringify_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Mapping):
        return json_lib.dumps(value, separators=(",", ":"), sort_keys=True)
    return str(value)


def flatten_items(mapping: Mapping[str, Any]) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for key, value in mapping.items():
        if value is None:
            continue
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for item in value:
                items.append((key, stringify_value(item)))
            continue
        items.append((key, stringify_value(value)))
    return items


def serialize_json_body(mapping: Mapping[str, Any]) -> str:
    return json_lib.dumps(mapping, ensure_ascii=False, separators=(",", ":"))


def encode_mapping(mapping: Mapping[str, Any], *, sort_query: bool = False) -> str:
    items = flatten_items(mapping)
    if sort_query:
        items.sort(key=lambda item: item[0])
    return urlencode(items, doseq=True)

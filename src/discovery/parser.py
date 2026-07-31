import json
from pathlib import Path
from typing import Union, Dict, Any
from src.api.schemas import ChangeRequest


KNOWN_COMPATIBLE_TYPES = {
    ("int", "bigint"),
    ("integer", "bigint"),
    ("float", "double"),
    ("varchar", "text"),
    ("string", "text"),
}

KNOWN_INCOMPATIBLE_TYPES = {
    ("decimal", "varchar"),
    ("decimal", "string"),
    ("numeric", "varchar"),
    ("timestamp", "int"),
    ("int", "varchar"),
    ("boolean", "int"),
}


def derive_semantic_mapping(old_type: str, new_type: str) -> str:
    """Derives semantic compatibility mapping between old and new data types."""
    old_t = old_type.lower()
    new_t = new_type.lower()
    if old_t == new_t:
        return "exact"
    if (old_t, new_t) in KNOWN_COMPATIBLE_TYPES:
        return "compatible"
    if (old_t, new_t) in KNOWN_INCOMPATIBLE_TYPES:
        return "incompatible"
    return "ambiguous"


def parse_change_request(source: Union[str, Path, Dict[str, Any]]) -> ChangeRequest:
    """
    Parses and validates a ChangeRequest payload from a JSON file path, JSON string, or dict.
    Supports 'field_rename' change type as per Evidence Gate spec.
    """
    if isinstance(source, (str, Path)):
        path = Path(source)
        if path.is_file():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = json.loads(str(source))
    elif isinstance(source, dict):
        data = source.copy()
    else:
        raise ValueError(f"Unsupported input type for parse_change_request: {type(source)}")

    req = ChangeRequest(**data)
    if req.semantic_mapping is None:
        req.semantic_mapping = derive_semantic_mapping(req.old_type, req.new_type)
    return req

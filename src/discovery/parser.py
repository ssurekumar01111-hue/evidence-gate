import json
from pathlib import Path
from typing import Union, Dict, Any
from src.api.schemas import ChangeRequest


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
        data = source
    else:
        raise ValueError(f"Unsupported input type for parse_change_request: {type(source)}")

    return ChangeRequest(**data)

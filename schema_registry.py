import json
import os
import re

import aiofiles
from jsonschema import validate

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
pattern = re.compile(r"(?<!^)(?=[A-Z])")


class SchemaRegistryValidationError(BaseException):
    def __init__(self, message: str):
        super().__init__(message)


class SchemaRegistry:
    @staticmethod
    async def validate_event(event_data: dict, event_name: str, version: int):
        paths = event_name.split(".")
        for path in paths:
            path = pattern.sub("_", path).lower()
        schema_path = os.path.join(ROOT_DIR, f"event_schemas/{paths[0]}/{paths[1]}/{version}.json")
        async with aiofiles.open(schema_path) as schema_file:
            schema_file_content = await schema_file.read()

        schema = json.loads(schema_file_content)
        validate(instance=event_data, schema=schema)

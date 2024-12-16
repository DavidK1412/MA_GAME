import os
import json
from dotenv import load_dotenv

load_dotenv()

def load_json_config(json_data):
    for key, value in json_data.items():
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            if value[2:-1] in os.environ:
                json_data[key] = os.getenv(value[2:-1], "")
        elif isinstance(value, dict):
            load_json_config(value)

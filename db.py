import json
from MiogestObject import MiogestObject

DATA_FILE = "db.json"

def load_objects():
    """Load Miogest objects from a JSON file."""
    try:
        with open(DATA_FILE, "r") as file:
            data = json.load(file)
            return {obj["code"]: MiogestObject.from_dict(obj) for obj in data}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_request_counts(data):
    """Save updated request counts to the JSON file."""
    # Convert MiogestObject instances to dictionaries
    serializable_data = [obj.to_dict() for obj in data.values()]
    with open(DATA_FILE, "w") as f:
        json.dump(serializable_data, f, indent=4)
        print("File successfully updated with data")
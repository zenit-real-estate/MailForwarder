import json
from MiogestObject import MiogestObject
from logger import logger

DATA_FILE = "db.json"

def load_objects():
    """Load Miogest objects from a JSON file."""
    try:
        with open(DATA_FILE, "r") as file:
            data = json.load(file)
            objects = {obj["code"]: MiogestObject.from_dict(obj) for obj in data}
            logger.main_logger.info(f"Successfully loaded {len(objects)} objects from database")
            return objects
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.log_warning(f"Database file not found or corrupted: {e}", "load_objects")
        logger.main_logger.info("Starting with empty database")
        return {}

def save_request_counts(data):
    """Save updated request counts to the JSON file."""
    try:
        # Convert MiogestObject instances to dictionaries
        serializable_data = [obj.to_dict() for obj in data.values()]
        with open(DATA_FILE, "w") as f:
            json.dump(serializable_data, f, indent=4)
        logger.main_logger.info(f"Successfully saved {len(serializable_data)} objects to database")
    except Exception as e:
        logger.log_error(f"Failed to save database: {e}", "save_request_counts")
        raise
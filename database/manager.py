from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Initialize database client
# Use a single client instance throughout the application
db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client.get_database("TeleFwdBot")

# Collections
managed_users = db.get_collection("managed_users")
forwarding_rules = db.get_collection("forwarding_rules")


async def add_managed_user(user_id: int, session_string: str):
    """Adds or updates a managed user in the database."""
    update_data = {
        '$set': {
            'session_string': session_string,
            'is_active': True
        }
    }
    result = await managed_users.update_one({'user_id': user_id}, update_data, upsert=True)
    if result.upserted_id:
        logger.info(f"Successfully added user: {user_id}")
    else:
        logger.info(f"Successfully updated user: {user_id}")
    return await get_user_by_id(user_id)


async def get_all_active_users():
    """Retrieves all active managed users from the database."""
    return await managed_users.find({'is_active': True}).to_list(length=None)


async def get_user_by_id(user_id: int):
    """Retrieves a single managed user by their ID."""
    return await managed_users.find_one({'user_id': user_id})


async def deactivate_user(user_id: int):
    """Deactivates a managed user and deletes all their forwarding rules."""
    # First, delete all associated rules
    await forwarding_rules.delete_many({'user_id': user_id})
    logger.info(f"Deleted all forwarding rules for user: {user_id}")

    # Then, deactivate the user
    result = await managed_users.update_one(
        {'user_id': user_id},
        {'$set': {'is_active': False}}
    )
    if result.modified_count > 0:
        logger.info(f"Deactivated user: {user_id}")
        return True
    logger.warning(f"Attempted to deactivate non-existent or already inactive user: {user_id}")
    return False


# --- Forwarding Rule Management ---

async def add_forwarding_rule(user_id: int, rule_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adds a new forwarding rule for a user.
    A rule is defined by sources, destinations, and optional filters.
    """
    rule_config['user_id'] = user_id
    
    # Ensure sources and destinations are lists
    if not isinstance(rule_config.get('source_chats'), list) or not isinstance(rule_config.get('destination_chats'), list):
        raise ValueError("source_chats and destination_chats must be lists of chat IDs.")

    # Optional: Add validation for other fields here if needed

    result = await forwarding_rules.insert_one(rule_config)
    logger.info(f"Added new forwarding rule with ID {result.inserted_id} for user {user_id}")
    return await forwarding_rules.find_one({'_id': result.inserted_id})


async def get_forwarding_rules_for_user(user_id: int) -> List[Dict[str, Any]]:
    """Retrieves all forwarding rules for a specific user."""
    return await forwarding_rules.find({'user_id': user_id}).to_list(length=None)


async def delete_forwarding_rule(rule_id: str) -> bool:
    """Deletes a forwarding rule by its unique _id."""
    from bson.objectid import ObjectId
    result = await forwarding_rules.delete_one({'_id': ObjectId(rule_id)})
    
    if result.deleted_count > 0:
        logger.info(f"Deleted forwarding rule with ID: {rule_id}")
        return True
    logger.warning(f"Attempted to delete non-existent rule with ID: {rule_id}")
    return False


async def get_rule_by_id(rule_id: str) -> Dict[str, Any]:
    """Retrieves a single rule by its unique _id."""
    from bson.objectid import ObjectId
    return await forwarding_rules.find_one({'_id': ObjectId(rule_id)})

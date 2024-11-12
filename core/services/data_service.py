import redis.asyncio as redis
import json
from core.configs import settings
import logging
import aiohttp

# Configure logging to track important events in Redis and Pub/Sub interactions
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RedisManager:
    """
    A class to manage asynchronous interactions with Redis. This class provides methods
    to save, retrieve, and delete session-specific data in Redis.
    """

    def __init__(self):
        """
        Initialize the RedisManager with the necessary Redis configuration.
        Establish a connection to the Redis server using host, port, and password.
        """
        self.redis_client = redis.Redis(settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_PASSWORD)
        # self.redis_client = redis.from_url(
        #     f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        #     password=settings.REDIS_PASSWORD,
        #     decode_responses=True
        # )

    async def save_to_redis(self, session_id: str, key: str, data: dict, prefix: str = "prefix"):
        """
        Save data to Redis under a key prefixed with the provided prefix and session ID.
        
        :param session_id: Unique identifier for the session.
        :param key: Specific key under the session to store data.
        :param data: The data to be stored in Redis.
        :param prefix: Optional prefix to group keys (default is 'prefix').
        """
        redis_key = f"{prefix}:{session_id}:{key}"
        await self.redis_client.set(redis_key, json.dumps(data), ex=3600)
        logging.info(f"Data saved to Redis with key: {redis_key}")

    async def get_from_redis(self, session_id: str, key: str, prefix: str = "prefix"):
        """
        Retrieve data from Redis based on the prefix, session ID, and key.
        
        :param session_id: Unique identifier for the session.
        :param key: Specific key under the session to retrieve data.
        :param prefix: Optional prefix to group keys (default is 'prefix').
        :return: The retrieved data, or None if not found.
        """
        redis_key = f"{prefix}:{session_id}:{key}"
        data = await self.redis_client.get(redis_key)  # Fetch the data from Redis
        if data:
            logging.info(f"Data retrieved from Redis with key: {redis_key}")
            return json.loads(data)  # Return the data after converting it from JSON format
        else:
            logging.warning(f"No data found in Redis for key: {redis_key}")
            return None

    async def delete_from_redis(self, session_id: str, key: str):
        """
        Delete specific data from Redis based on the session ID and key.
        
        :param session_id: Unique identifier for the session.
        :param key: Specific key under the session to delete data.
        """
        redis_key = f"{session_id}:{key}"
        await self.redis_client.delete(redis_key)  # Delete the specified key from Redis
        logging.info(f"Data deleted from Redis for key: {redis_key}")

# Asynchronous function to send data to an external service (facilitate-request)
async def send_to_service(service_url, data, session_id, service_name):
    """
    Asynchronous function to send data to an external service (HTML process or URL parsing).
    
    :param service_url: The URL of the external service.
    :param data: The data payload to be sent.
    :param session_id: The session ID for tracking.
    :param user_id: The user ID for tracking.
    :param service_name: The name of the service for logging.
    """
    logging.info(f"Sending data to {service_name} API for session: {session_id}")
    redis_manager = RedisManager()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(service_url, json=data) as response:
                if response.status == 200:
                    logging.info(f"{service_name} API call successful for session: {session_id}")
                    result = await response.json()
                    await redis_manager.save_to_redis(session_id, f"{service_name.lower()}_result", result, prefix="temp")
                else:
                    error_msg = await response.text()
                    logging.error(f"Failed to call {service_name} API: {response.status}, {error_msg}")
                    raise Exception(f"Failed to call {service_name} API: {response.status}, {error_msg}")
    
    except Exception as e:
        logging.error(f"Error occurred while calling {service_name} API for session: {session_id} - {str(e)}")
        raise e
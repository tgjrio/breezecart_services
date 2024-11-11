import logging

from fastapi import FastAPI
from core.configs import settings
from core.services import data_service as ds

# Initialize RedisManager and PubSubManager
redis_manager = ds.RedisManager()


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize FastAPI application
app = FastAPI()

@app.post("/pubsub/events")
async def process_url_events(message_json: dict):
    """
    Function to process Pub/Sub events and handle different phases of the workflow.
    
    :param message_json: Decoded Pub/Sub message containing session data and phase info.
    """
    session_id = message_json.get("session_id")
    phase = message_json.get("phase")

    logging.info(f"Processing phase: {phase} for session: {session_id}")

    # Store the initial message data in Redis
    await redis_manager.save_to_redis(session_id, "event_data", message_json, prefix="temp")

    # Handle the session state transitions
    # await redis_manager.save_to_redis(session_id, "event_data", message_json, prefix="session")

    # Handle the different phases
    try:
        if phase == "validation_complete":
            # Call HTML processing service
            await ds.send_to_service(settings.PROCESS_HTML_URL, message_json, session_id, "HTML Processing")

        elif phase == "chat_gpt_ingest":
            # Call URL parsing service
            await ds.send_to_service(settings.CHAT_GPT_INGEST, message_json, session_id,"Chat GPT Processing")

        else:
            # Invalid phase handling
            logging.error(f"Unknown phase: {phase} for session: {session_id}")
            raise ValueError(f"Unknown phase: {phase}")

        # Publish the processed event back to Pub/Sub for further processing
        # await pubsub_manager.publish_to_pubsub(settings.PUBSUB_TOPIC_DATA_COLLECT, message_json)
        # logging.info(f"Published update to Pub/Sub for session: {session_id}")

    except Exception as e:
        logging.error(f"Error processing Pub/Sub event for session: {session_id} - {str(e)}")
        raise e

# This block is executed when running the script directly, starting the FastAPI app using Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)


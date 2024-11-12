from core.services import data_service as ds
from core.configs import schemas
from fastapi import FastAPI, BackgroundTasks
from core.services import background_service as bt
import logging

# Initialize RedisManager to handle storing and retrieving data from Redis
redis_manager = ds.RedisManager()

# Initialize FastAPI application
app = FastAPI()

# Route to process the HTML (retrieve submission from Redis, process HTML, and store in Redis)
@app.post("/process-html") 
async def process_html(submission: schemas.SubmissionRequest, background_tasks: BackgroundTasks):
    try:
        session_id = submission.session_id  # Extract the session ID
        url = str(submission.url)
        user_id = submission.user_id
        logging.info(f"Received submission: session_id={session_id}, url={url}, user_id={user_id}")

        # Prepare session data
        session_data = {
            "session_id": session_id,
            "url": url,
            "user_id": user_id,
        }
        logging.info("Attempting to save session data to Redis...")
        await redis_manager.save_to_redis(session_id, "submission", session_data, prefix="temp")
        logging.info("Session data saved successfully.")

        # Retrieve data for verification
        saved_data = await redis_manager.get_from_redis(session_id, "submission", prefix="temp")
        if saved_data is None:
            logging.error("Failed to retrieve session data from Redis.")
            return {"error": "Failed to save session data to Redis"}
        logging.info("Session data retrieved successfully.")

        # Add background task
        background_tasks.add_task(bt.background_process_html, submission)
        return {"message": "HTML processing has been started in the background."}
    except Exception as e:
        logging.error(f"Error in process_html: {str(e)}")
        raise e

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
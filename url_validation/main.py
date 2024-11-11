import logging
from fastapi import FastAPI, HTTPException
from core.configs import schemas, settings
from core.services import data_service as ds


# Set up logging to track important events and errors throughout the app
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize FastAPI application
app = FastAPI()

# Initialize RedisManager
redis_manager = ds.RedisManager()

# Route for starting the URL processing workflow (validation and storing submission in Redis)
@app.post("/start")
async def start_processing(submission: schemas.SubmissionRequest):
    """
    API route to validate the submitted URL, store submission data in Redis, and notify the user.
    This function initiates the workflow for processing the submitted URL.
    
    :param submission: The validated submission request containing session_id, user_id, and the URL.
    :return: A message indicating the validation result and stored session data.
    """
    try:
        logging.info(f"Starting validation for session: {submission.session_id}")

        # Validate that the URL is not empty; if invalid, raise an HTTP exception
        if not submission.url:
            logging.error(f"Invalid URL submitted for session: {submission.session_id}")
            raise HTTPException(status_code=400, detail="Invalid URL")

        # Prepare the message data to be saved in Redis
        message_data = {
            "session_id": submission.session_id,
            "url": str(submission.url),
            "user_id": submission.user_id,
            "phase": "validation_complete"
        }

        # Save the submission data to Redis under the key "submission" for the given session ID
        await redis_manager.save_to_redis(submission.session_id, "submission", message_data, prefix="temp")
        logging.info(f"Submission stored in Redis for session: {submission.session_id}")

        # Send data to the facilitate-request endpoint using send_to_service
        await ds.send_to_service(settings.FACILITATE_EVENTS, message_data, submission.session_id, "Facilitate Request")

        # Return a success message along with the stored session data retrieved from Redis
        return {
            "message": "Validation successful", 
            "session_data": await redis_manager.get_from_redis(submission.session_id, "submission", prefix="temp")
        }

    # Handle any unexpected errors during the submission process
    except Exception as e:
        logging.error(f"Error processing submission for session: {submission.session_id} - {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# This block is executed when running the script directly, starting the FastAPI app using Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
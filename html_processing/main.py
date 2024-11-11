from core.services import data_service as ds
from core.configs import schemas
from fastapi import FastAPI, BackgroundTasks
from core.services import background_service as bt

# Initialize RedisManager to handle storing and retrieving data from Redis
redis_manager = ds.RedisManager()


# Initialize FastAPI application
app = FastAPI()

# Route to process the HTML (retrieve submission from Redis, process HTML, and store in Redis)
@app.post("/process-html") 
async def process_html(submission: schemas.SubmissionRequest, background_tasks: BackgroundTasks):
    """
    API route to handle the HTML processing for a submitted URL.
    The processing is done in the background.
    
    :param submission: The submission request, containing session_id, user_id, and the URL.
    :param background_tasks: BackgroundTasks instance for executing tasks asynchronously.
    :return: JSON response indicating that HTML processing has started.
    """
    
    session_id = submission.session_id  # Extract the session ID from the submission
    
    # Prepare the session data to be saved in Redis (this is important for processing in later steps)
    session_data = {
        "session_id": session_id,  # Session ID to uniquely identify the request
        "url": str(submission.url),  # The URL being submitted, converted to a string format
        "user_id": submission.user_id,  # The user ID making the submission
    }
    
    # Save the session data to Redis with the key "submission" under the session ID
    await redis_manager.save_to_redis(session_id, "submission", session_data, prefix="temp")

    # Retrieve the data back from Redis to ensure it was saved correctly
    saved_data = await redis_manager.get_from_redis(session_id, "submission", prefix="temp")
    
    # If the data was not successfully saved, return an error message
    if saved_data is None:
        return {"error": "Failed to save session data to Redis"}

    # Add the HTML processing task to the background queue
    background_tasks.add_task(bt.background_process_html, submission)

    # Return a success message to the client, indicating that HTML processing has started in the background
    return {"message": "HTML processing has been started in the background."}
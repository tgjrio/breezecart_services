from core.configs import settings
from core.configs import schemas
from core.services import data_service as ds

from . import recipe_service as rp
from fastapi import HTTPException
import logging


# Initialize data managers
redis_manager = ds.RedisManager()

# Background task for processing HTML
async def background_process_html(submission: schemas.SubmissionRequest):
    """
    A background task that processes the HTML of a submitted URL.
    The task fetches the HTML content, scrapes recipe data, and stores it in Redis.
    
    :param submission: A validated request containing user, session, and URL information.
    """
    
    logging.info(f"Starting HTML processing for session: {submission.session_id}")

    # Retrieve previously stored submission data from Redis using session ID
    stored_submission = await redis_manager.get_from_redis(submission.session_id, "submission", prefix="temp")
    
    # If no data is found in Redis, raise an HTTP 404 error
    if not stored_submission:
        logging.error(f"Session {submission.session_id} not found in Redis.")
        raise HTTPException(status_code=404, detail="Session not found or data missing")

    submitted_url = str(submission.url)  # Store the submitted URL

    try:        
        logging.info(f"Scraping URL for recipe data: {submission.session_id}")

        # Initialize the RecipeScraper to handle the recipe scraping process
        scraper = rp.RecipeScraper(submitted_url, submission.session_id, submission.user_id, redis_manager)

        # Fetch the HTML content from the submitted URL
        await scraper.fetch_page_content()

        # Extract recipe image and name from the fetched HTML
        recipe_image, recipe_name, recipe_video_url = await scraper.extract_recipe_image_name_video()

        # Extract recipe Ingredients
        recipe_ingredients = await scraper.extract_ingredients()

        # Extract recipe nutrition and tutorial video URL
        recipe_nutrition = await scraper.extract_nutrition_data()

    except Exception as e:
        # In case of errors during HTML fetching or parsing, log the error
        logging.error(f"Error extracting recipe data for session {submission.session_id}: {str(e)}")
        recipe_image, recipe_name = None, None

    # Check if the recipe name and image were extracted successfully
    if not recipe_image or not recipe_name:
        # If no recipe image or name is found, log the issue
        logging.warning(f"No recipe image or name found for session: {submission.session_id}")

    # Log the extracted recipe details
    logging.info(f"Recipe: {recipe_name}")
    logging.info(f"Recipe Image: {recipe_image}")
    logging.info(f"Recipe Video URL: {recipe_video_url}")
    logging.info(f"Recipe Ingredients: {recipe_ingredients}")
    logging.info(f"Recipe Nutrition: {recipe_nutrition}")

    # Prepare the formatted data to be stored in Redis
    raw_data = {
        "user_id": submission.user_id,
        "session_id": submission.session_id,
        "recipe_url": str(submitted_url),
        "recipe_name": recipe_name,
        "recipe_image": recipe_image,
        "recipe_video_url" : recipe_video_url,
        "recipe_ingredients_raw" : recipe_ingredients,
        "recipe_nutrition_raw" : recipe_nutrition,
        "bucket" : 'raw_processed_data'
    }

    # Save the processed HTML data to Redis under the "processed_html" key for the current session
    await redis_manager.save_to_redis(submission.session_id, "processed_html", raw_data, prefix="temp")

    gpt_request_data = {
        "user_id": submission.user_id,
        "session_id": submission.session_id,
        "recipe_name": recipe_name,
        "redis_key": "processed_html",
        "phase": "chat_gpt_ingest"
    }

    # Publish an event to Pub/Sub to indicate the completion of the HTML processing phase
    await ds.send_to_service(settings.FACILITATE_EVENTS, gpt_request_data, submission.session_id, "Facilitate Request")

    logging.info(f"HTML processing complete for session: {submission.session_id}")
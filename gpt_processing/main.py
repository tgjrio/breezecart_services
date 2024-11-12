from fastapi import FastAPI
import logging
import json
from core.configs import settings
from core.configs import schemas
from core.services import data_service as ds
from core.services import gpt_service as gpt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize RedisManager to handle storing and retrieving data from Redis
redis_manager = ds.RedisManager()
pubsub_manager = ds.PubSubManager()

# Initialize FastAPI application
app = FastAPI()

@app.post("/process-gpt")
async def process_gpt(gpt_request: schemas.ChatGptRequest):

    session_id = gpt_request.session_id
    redis_key = gpt_request.redis_key

    # Use Get From Redis method to extract object data
    formatted_data = await redis_manager.get_from_redis(session_id, redis_key, prefix="temp")

    recipe_name = formatted_data['recipe_name']
    recipe_ingredients = formatted_data['recipe_ingredients_raw']
    recipe_nutrition = formatted_data['recipe_nutrition_raw']
    
    clean_ingredients = await gpt.standardize_ingredients(recipe_name, recipe_ingredients)
    logging.info("Ingredients successfully processed")
    clean_nutrition = await gpt.standardize_nutrition(recipe_name, recipe_nutrition)
    logging.info("Nutrition successfully processed")

# Check if clean_ingredients is a string and convert only if necessary
    if isinstance(clean_ingredients, str):
        try:
            clean_ingredients = json.loads(clean_ingredients)
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding clean_ingredients: {e}")
            raise

    # Check if clean_nutrition is a string and convert only if necessary
    if isinstance(clean_nutrition, str):
        try:
            clean_nutrition = json.loads(clean_nutrition)
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding clean_nutrition: {e}")
            raise

    # Clean Data
    clean_data = {
        "user_id": gpt_request.user_id,
        "session_id": gpt_request.session_id,
        "recipe_url": formatted_data['recipe_url'],
        "recipe_name": gpt_request.recipe_name,
        "recipe_image": formatted_data['recipe_image'],
        "recipe_video_url" : formatted_data['recipe_video_url'],
        "recipe_ingredients_clean" : clean_ingredients,
        "recipe_nutrition_clean" : clean_nutrition,
        "bucket" : 'clean_processed_data'
    }

    # serialized_clean_data = json.dumps(clean_data)

    logging.info(f"Serialized Clean Object: {clean_data}")

    # Send to Redis
    await redis_manager.save_to_redis(session_id, 'clean_processed_data', clean_data, prefix="temp")

    # Send to Pub/Sub Topic Clean_data
    await pubsub_manager.publish_to_pubsub(settings.PUBSUB_TOPIC_DATA_COLLECT, clean_data)    

# This block is executed when running the script directly, starting the FastAPI app using Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
    


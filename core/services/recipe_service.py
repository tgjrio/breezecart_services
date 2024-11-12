import aiohttp
from bs4 import BeautifulSoup
import json
import logging
import html
import ssl
from core.services.data_service import RedisManager


# Configure logging settings to track important events and errors during execution
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class RecipeScraper:
    """
    A class to scrape recipe data from a given URL. The data is fetched asynchronously,
    parsed with BeautifulSoup, and extracted from JSON-LD structured data on the page. Results are stored in Redis
    and published via Pub/Sub. Server-Sent Events (SSE) is used for real-time feedback to the client.
    """
    
    def __init__(self, url, session_id, user_id, redis_manager: RedisManager):
        """
        Initialize the RecipeScraper object with required attributes.
        
        :param url: The URL of the recipe page to be scraped.
        :param session_id: A unique session identifier for the current request.
        :param user_id: The ID of the user making the request.
        :param redis_manager: Instance of RedisManager to store scraped data in Redis.
        :param pubsub_manager: Instance of PubSubManager to publish data to Pub/Sub.
        """
        self.url = url
        self.session_id = session_id
        self.user_id = user_id
        self.redis_manager = redis_manager
        
        # User-Agent header to simulate a request from a regular browser
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.soup = None  # Placeholder for the BeautifulSoup object

    async def fetch_page_content(self):
        """
        Fetch the content of the URL page asynchronously and parse it using BeautifulSoup.
        The content is also sent to the client via SSE for real-time feedback.
        """
        logging.info(f"Fetching page content for URL: {self.url}")
        try:
            # SSL context configuration to bypass SSL certificate verification
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE  # Ignore SSL cert validation (use with caution)

            # Open an asynchronous HTTP session to fetch the page content
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url, headers=self.headers, ssl=ssl_context) as response:
                    if response.status != 200:
                        # Handle non-successful HTTP responses and notify the client
                        raise Exception(f"HTTP error occurred: {response.status}")
                    
                    # Read and parse the HTML content of the page
                    content = await response.text()
                    self.soup = BeautifulSoup(content, 'html.parser')
                    logging.info(f"Successfully fetched and parsed content for URL: {self.url}")
                    
                    # Notify the client of the successful page fetch
        except Exception as e:
            # Log and notify the client about any errors during the page fetch process
            logging.error(f"Error fetching page content for URL: {self.url} - {str(e)}")
            raise

    async def extract_ingredients(self):
        """
        Extract the 'recipeIngredient' list from JSON-LD data embedded on the page.
        This method searches through script tags and identifies structured data in JSON format.
        The results are stored in Redis and published to Pub/Sub.
        """
        logging.info(f"Extracting ingredients from URL: {self.url}")
        if not self.soup:
            raise Exception("Soup object not initialized. Call fetch_page_content first.")

        # Find all script tags containing JSON-LD structured data
        script_tags = self.soup.find_all('script', type='application/ld+json')

        for script_tag in script_tags:
            try:
                script_content = script_tag.string.strip()
                if script_content.endswith(';'):
                    script_content = script_content[:-1]

                json_data = json.loads(script_content)

                if 'recipeIngredient' in json_data:
                    logging.info("Ingredients successfully extracted from JSON-LD.")
                    await self.redis_manager.save_to_redis(self.session_id, "ingredients", json_data['recipeIngredient'], prefix="temp")
                    # await self.pubsub_manager.publish_to_pubsub(settings.PUBSUB_TOPIC_HTML_PROCESS, {
                    #     "session_id": self.session_id,
                    #     "user_id": self.user_id,
                    #     "ingredients": json_data['recipeIngredient']
                    # })
                    return json_data['recipeIngredient']

                if isinstance(json_data, list):
                    for item in json_data:
                        if 'recipeIngredient' in item:
                            logging.info("Ingredients successfully extracted from JSON-LD list.")
                            await self.redis_manager.save_to_redis(self.session_id, "ingredients", item['recipeIngredient'], prefix="temp")
                            # await self.pubsub_manager.publish_to_pubsub(settings.PUBSUB_TOPIC_HTML_PROCESS, {
                            #     "session_id": self.session_id,
                            #     "user_id": self.user_id,
                            #     "ingredients": item['recipeIngredient']
                            # })
                            return item['recipeIngredient']

                if '@graph' in json_data:
                    for graph_item in json_data['@graph']:
                        if 'recipeIngredient' in graph_item:
                            logging.info("Ingredients successfully extracted from JSON-LD graph.")
                            await self.redis_manager.save_to_redis(self.session_id, "ingredients", graph_item['recipeIngredient'], prefix="temp")
                            # await self.pubsub_manager.publish_to_pubsub(settings.PUBSUB_TOPIC_HTML_PROCESS, {
                            #     "session_id": self.session_id,
                            #     "user_id": self.user_id,
                            #     "ingredients": graph_item['recipeIngredient']
                            # })
                            return graph_item['recipeIngredient']

            except json.JSONDecodeError as e:
                logging.error(f"Error parsing JSON-LD block: {e}")
                continue

        raise Exception("No recipeIngredient found in JSON-LD data.")
    
    async def extract_nutrition_data(self):
        """Extract the nutrition, recipeCategory, recipeYield, recipeName, and author from JSON-LD structured data on the page."""
        logging.info(f"Extracting nutrition data from URL: {self.url}")
        if not self.soup:
            raise Exception("Soup object not initialized. Call fetch_page_content first.")

        # Find all <script> tags with type="application/ld+json"
        script_tags = self.soup.find_all('script', type='application/ld+json')

        # Iterate over each JSON-LD <script> tag
        for script_tag in script_tags:
            try:
                script_content = script_tag.string.strip()

                # Remove any trailing semicolons or non-JSON characters
                if script_content.endswith(';'):
                    script_content = script_content[:-1]

                # Attempt to parse the cleaned JSON
                json_data = json.loads(script_content)

                # Check if the JSON is a list
                if isinstance(json_data, list):
                    json_data = json_data[0]  # Access the first item in the list

                # Extract fields
                nutrition_data = json_data.get('nutrition', None)
                recipe_category = json_data.get('recipeCategory', None)
                recipe_yield = json_data.get('recipeYield', None)
                recipe_name = json_data.get('name', None)
                author = json_data.get('author', [{}])[0].get('name', None)

                # If no nutrition data found, check deeper within possible nested structures
                if not nutrition_data and '@graph' in json_data:
                    for graph_item in json_data['@graph']:
                        if 'nutrition' in graph_item:
                            nutrition_data = graph_item['nutrition']
                            break  # Found nutrition data, break the loop

                # If nutrition data is found, append additional data
                if nutrition_data:
                    # Remove '@type' from nutrition data
                    nutrition_data.pop('@type', None)

                    # Add recipe category and recipe yield
                    if recipe_category:
                        nutrition_data['recipeCategory'] = recipe_category
                    if recipe_yield:
                        nutrition_data['recipeYield'] = recipe_yield

                    # Add recipe name and author
                    if recipe_name:
                        nutrition_data['recipeName'] = html.unescape(recipe_name)  # Unescape HTML entities
                    if author:
                        nutrition_data['author'] = author

                    # await self.pubsub_manager.publish_to_pubsub(settings.PUBSUB_TOPIC_HTML_PROCESS, {
                    #             "session_id": self.session_id,
                    #             "user_id": self.user_id,
                    #             "nutrition_data": nutrition_data
                    #         })

                    return nutrition_data

            except json.JSONDecodeError as e:
                logging.error(f"Error parsing JSON-LD block: {e}")
                continue  # Skip to the next block if this one can't be parsed

        # If no nutrition data is found
        raise Exception("No nutrition data found in JSON-LD data.")

    async def extract_recipe_image_name_video(self):
        """
        Extract the main recipe image, recipe name, and video content URL from the JSON-LD structured data on the page.
        The data is stored in Redis and published to Pub/Sub for further processing.
        """
        logging.info(f"Extracting recipe name, image, and video from URL: {self.url}")
        if not self.soup:
            raise Exception("Soup object not initialized. Call fetch_page_content first.")

        script_tags = self.soup.find_all('script', type='application/ld+json')

        for script_tag in script_tags:
            try:
                script_content = script_tag.string.strip()
                if script_content.endswith(';'):
                    script_content = script_content[:-1]

                json_data = json.loads(script_content)

                if isinstance(json_data, list):
                    for item in json_data:
                        recipe_image, recipe_name, recipe_video_url = self.process_recipe_data(item)
                        if recipe_image and recipe_name:
                            logging.info(f"Successfully extracted recipe name: {recipe_name}, image, and video URL.")
                            await self.redis_manager.save_to_redis(
                                self.session_id, 
                                "recipe_info", {
                                    "name": recipe_name,
                                    "image": recipe_image,
                                    "video_url": recipe_video_url
                                }, 
                                prefix="temp"
                            )
                            # await self.pubsub_manager.publish_to_pubsub(settings.PUBSUB_TOPIC_HTML_PROCESS, {
                            #     "session_id": self.session_id,
                            #     "user_id": self.user_id,
                            #     "recipe_name": recipe_name,
                            #     "recipe_image": recipe_image,
                            #     "recipe_video_url": recipe_video_url
                            # })
                            return recipe_image, recipe_name, recipe_video_url

                else:
                    recipe_image, recipe_name, recipe_video_url = self.process_recipe_data(json_data)
                    if recipe_image and recipe_name:
                        logging.info(f"Successfully extracted recipe name: {recipe_name}, image, and video URL.")
                        await self.redis_manager.save_to_redis(
                            self.session_id, 
                                "recipe_info", {
                                "name": recipe_name,
                                "image": recipe_image,
                                "video_url": recipe_video_url
                            },
                            prefix="temp"
                        )
                        # await self.pubsub_manager.publish_to_pubsub(settings.PUBSUB_TOPIC_HTML_PROCESS, {
                        #     "session_id": self.session_id,
                        #     "user_id": self.user_id,
                        #     "recipe_name": recipe_name,
                        #     "recipe_image": recipe_image,
                        #     "recipe_video_url": recipe_video_url
                        # })
                        return recipe_image, recipe_name, recipe_video_url

            except json.JSONDecodeError as e:
                logging.error(f"Error parsing JSON-LD: {e}")
                continue

        raise Exception("No recipe name, image, or video URL found in JSON-LD data.")

    def find_video_content_url(self, json_data):
        """
        Recursively search for the contentUrl within objects of type 'VideoObject'.
        
        :param json_data: The JSON data to search through.
        :return: The contentUrl for the video if found, otherwise None.
        """
        if isinstance(json_data, dict):
            # Check if this dictionary is a VideoObject
            if json_data.get('@type') == 'VideoObject':
                return json_data.get('contentUrl', None)
            
            # If not, keep searching within the values
            for key, value in json_data.items():
                if isinstance(value, (dict, list)):
                    result = self.find_video_content_url(value)
                    if result:
                        return result

        elif isinstance(json_data, list):
            for item in json_data:
                result = self.find_video_content_url(item)
                if result:
                    return result

        return None

    def process_recipe_data(self, json_data):
        """
        Process a single JSON-LD object and extract the recipe name, image, and video content URL from it.

        :param json_data: The JSON-LD data object containing recipe information.
        :return: A tuple (recipe_image, recipe_name, recipe_video_url) if available, else (None, None, None).
        """
        recipe_name = json_data.get('name')  # Extract recipe name
        recipe_image = json_data.get('image')  # Extract recipe image
        
        # Use the specific function to find the video contentUrl
        recipe_video_url = self.find_video_content_url(json_data)

        if '@graph' in json_data:
            for graph_item in json_data['@graph']:
                graph_type = graph_item.get('@type')

                if isinstance(graph_type, list):
                    if "Recipe" in graph_type:
                        recipe_name = graph_item.get('name', recipe_name)
                        recipe_image = graph_item.get('image', recipe_image)
                elif graph_type == "Recipe":
                    recipe_name = graph_item.get('name', recipe_name)
                    recipe_image = graph_item.get('image', recipe_image)

        if isinstance(recipe_image, list):
            recipe_image = recipe_image[-1]

        if isinstance(recipe_image, dict) and 'url' in recipe_image:
            recipe_image = recipe_image['url']

        return recipe_image, recipe_name, recipe_video_url
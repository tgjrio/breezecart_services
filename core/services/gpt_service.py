import logging
import json
from core.configs import settings
from core.configs import prompts

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def standardize_ingredients(recipe_name, recipe_ingredients):
    try:
        response = settings.OPENAI_CLIENT.chat.completions.create(
            model="gpt-4o",
            messages=[
                {f"role": "system", "content": prompts.prompt_ingredients},
                {"role": "user", "content": f"Here's the ingredients: {recipe_ingredients}"},
            ]
        )
        # Ensure the response has content before parsing
        if not response.choices or not response.choices[0].message.content:
            raise ValueError("Empty response from OpenAI API")

        # Log the raw response for debugging
        summary = response.choices[0].message.content
        # Log the parsed summary for debugging
        logging.info(f"Parsed summary: {summary}")

         # send gpt metadata to pub/sub

    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error while summarizing transcription: {e}, response: {summary}")
        raise RuntimeError(f"JSON decode error while summarizing transcription: {e}")
    except KeyError as e:
        logging.error(f"Key error: 'summary' key not found in the response: {e}, response: {summary}")
        raise RuntimeError(f"Key error: 'summary' key not found in the response: {e}")
    except Exception as e:
        logging.error(f"Error summarizing transcription: {e}")
        raise RuntimeError(f"Error summarizing transcription: {e}")

    return summary

async def standardize_nutrition(recipe_name, recipe_nutrition):
    try:
        response = settings.OPENAI_CLIENT.chat.completions.create(
            model="gpt-4o",
            messages=[
                {f"role": "system", "content": prompts.prompt_nutrition},
                {"role": "user", "content": f"Here's the nutrition: {recipe_nutrition}"},
            ]
        )
        # Ensure the response has content before parsing
        if not response.choices or not response.choices[0].message.content:
            raise ValueError("Empty response from OpenAI API")

        # Log the raw response for debugging
        summary = response.choices[0].message.content
        # Log the parsed summary for debugging
        logging.info(f"Parsed summary: {summary}")

        # send gpt metadata to pub/sub

    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error while summarizing transcription: {e}, response: {summary}")
        raise RuntimeError(f"JSON decode error while summarizing transcription: {e}")
    except KeyError as e:
        logging.error(f"Key error: 'summary' key not found in the response: {e}, response: {summary}")
        raise RuntimeError(f"Key error: 'summary' key not found in the response: {e}")
    except Exception as e:
        logging.error(f"Error summarizing transcription: {e}")
        raise RuntimeError(f"Error summarizing transcription: {e}")

    return summary
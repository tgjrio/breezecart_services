prompt_ingredients = """
I have an ingredient list from a recipe, and I need it transformed into a structured list of dictionaries, ready for Pub/Sub and Redis ingestion. The response must be a JSON string.

Structure Requirements:
- Each ingredient should be a dictionary with fields:
    • ingredient: the name of the ingredient
    • quantity: the numeric value of the ingredient (e.g., 1, 0.5)
    • unit: the unit of measurement (e.g., “cup”, “g”). If there’s no clear unit, set the unit to “user discretion”.
    • category: the category of the ingredient (e.g., “spice”, “veggie", "meat")
    
Example:
"[
    {"ingredient": "sweet Italian sausage", "quantity": 1, "unit": "pound", "category":"meat"},
    {"ingredient": "lean ground beef", "quantity": 0.75, "unit": "pound", "category":"meat"},
    {"ingredient": "minced onion", "quantity": 0.5, "unit": "cup", "category":"spice"},
]"
  
Processing Rules:
- For whole items like fruits, vegetables, or eggs, use “units” as the unit.
- Remove any preparation instructions (like peeled, cored, or chopped).
- If the ingredient calls for a can of something, just use the number of ounces recommended.

Response Rules:
- Your response should only include the structured list of dictionaries as described above. don't put any markdown content
- This data must be clean and ready for ingestion into Pub/Sub and Redis for a grocery list generation service.

"""

prompt_nutrition = """
I have a dictionary of nutrition facts from a recipe, and I need it transformed into a structured list of dictionaries, ready for Pub/Sub and Redis ingestion. The response must be a JSON string.

Structure Requirements:
- Each nutrition fact should be a dictionary with fields:
    • name: the name of the nutrient (e.g., “calories”, “carbohydrateContent”)
    • quantity: the numeric value of the nutrient (e.g., 315, 59). If there is no numeric value, set the quantity to 0.0.
    • unit: the unit of the nutrient (e.g., “kcal”, “g”, “mg”). If there is no clear unit, set the unit to “user discretion”.


Example:
"[
	{"name": "calories", "quantity": 315.0, "unit": "kcal"},
	{"name": "carbohydrateContent", "quantity": 59.0, "unit": "g"},
	{"name": "proteinContent", "quantity": 3.0, "unit": "g"},
]"

Processing Rules:
- Remove any extra text like “about” or “approximately” from the values.

Response Rules:
- Your response should only include the structured list of dictionaries as described above. don't put any markdown content
- This data must be clean and ready for ingestion into Pub/Sub and Redis for a nutrition tracking service.

"""
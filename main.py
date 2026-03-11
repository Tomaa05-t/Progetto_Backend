import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from deep_translator import GoogleTranslator

# 1. Caricamento configurazioni
load_dotenv()
API_KEY = os.getenv("SPOONACULAR_KEY")
BASE_URL = "https://api.spoonacular.com/recipes/complexSearch"

# 2. Inizializzazione applicazioni e traduttore
app = FastAPI()

# 3. Configura il CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_credentials=True,
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Il server del Food Tracker è attivo!"}

@app.get("/api/search")
def search_food(query: str):
    query_inglese = GoogleTranslator(source='it', target='en').translate(query)

    print(f"DEBUG: Utente ha cercato '{query}', tradotto in '{query_inglese}'")

    params = {
        "query": query_inglese,
        "apiKey": API_KEY,
        "addRecipeNutrition": "true",
        "number": 5
    }
    
    response = requests.get(BASE_URL, params=params)
    
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Errore API esterna")

    data = response.json()
    
    cleaned_data = []
    for recipe in data.get("results", []):
        nutrients = recipe.get("nutrition", {}).get("nutrients", [])
        
        calories = next((item["amount"] for item in nutrients if item["name"] == "Calories"), 0)
        protein = next((item["amount"] for item in nutrients if item["name"] == "Protein"), 0)

        cleaned_data.append({
            "id": recipe["id"],
            "title": recipe["title"],
            "image": recipe.get("image", ""),
            "calories": calories,
            "protein": protein,
            "source_url": f"https://spoonacular.com/recipes/{recipe['title'].replace(' ', '-').lower()}-{recipe['id']}"
        })
    
    return cleaned_data

@app.get("/api/recipe/{recipe_id}/instructions")
def get_instructions(recipe_id: int):
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/analyzedInstructions"
    params = {"apiKey": API_KEY}
    response = requests.get(url, params=params)
    return response.json()
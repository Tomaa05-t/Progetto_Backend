import os
import requests
from fastapi import FastAPI, HTTPException #il motore che crea il server
from fastapi.middleware.cors import CORSMiddleware 
from dotenv import load_dotenv #serve a leggere l'api key
from deep_translator import GoogleTranslator #traduttore

# carica la chiave segreta da .env
load_dotenv()
API_KEY = os.getenv("SPOONACULAR_KEY")
BASE_URL = "https://api.spoonacular.com/recipes/complexSearch"

# accende il server
app = FastAPI()

# dice al server di accettare richieste da qualsiasi origine 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_credentials=True,
    allow_headers=["*"],
)

#controllo che il server sia attivo
@app.get("/") #chiamo questa funzione quando inserisco l'url su internet
def read_root():
    return {"message": "Il server del Food Tracker è attivo!"}

@app.get("/api/search") #l'oggetto app che ho creato prima, quando riceve una richiesta GET sull'indirizzo /api/search deve eseguire la funzione search_food
def search_food(query: str): #definisco la funzione che accetta l'ingrediente come parametro
    query_inglese = GoogleTranslator(source='it', target='en').translate(query)  #traduci la query in inglese

    print(f"DEBUG: Utente ha cercato '{query}', tradotto in '{query_inglese}'")

    #preparo cosa il serve deve inviare alla API esterna
    params = {
        "query": query_inglese, #uso la query in inglese che ho tradotto 
        "apiKey": API_KEY, #uso la chiave segreta che ho ottenuto da spoonacular
        "addRecipeNutrition": "true", #chiedo alla API di includere le informazioni nutrizionali
        "number": 5 #chiedo alla API di restituire al massimo 5 ricette
    }
    
    response = requests.get(BASE_URL, params=params) #faccio la richiesta alla API esterna con i parametri che ho preparato
    
    if response.status_code != 200: #controllo se la risposta è andata a buon fine, se no restituisco un errore al client
        raise HTTPException(status_code=500, detail="Errore API esterna")

    data = response.json() #prendo i dati che mi ha restituito la API esterna e li trasformo in un formato che posso usare
    
    cleaned_data = [] #creo una lista vuota dove salvo i dati 
    for recipe in data.get("results", []):#per ogni ricetta nella lista dei risultati
        nutrients = recipe.get("nutrition", {}).get("nutrients", [])#prendo la lista dei nutrienti, se non c'è metto una lista vuota
        
        calories = next((item["amount"] for item in nutrients if item["name"] == "Calories"), 0)#cerco nella lista dei nutrienti quello che si chiama "Calories" e prendo il suo valore, se non lo trovo metto 0
        protein = next((item["amount"] for item in nutrients if item["name"] == "Protein"), 0)

        cleaned_data.append({ #creo un nuovo dizionario con solo le informazioni che mi interessano e lo aggiungo alla lista dei dati puliti
            "id": recipe["id"],
            "title": recipe["title"],
            "image": recipe.get("image", ""),
            "calories": calories,
            "protein": protein,
            "source_url": f"https://spoonacular.com/recipes/{recipe['title'].replace(' ', '-').lower()}-{recipe['id']}"
        })
    
    return cleaned_data

@app.get("/api/recipe/{recipe_id}/instructions")#mi serve per leggere nel mio sito le ricette date dall'api
def get_instructions(recipe_id: int):#definisco la funzione che accetta l'id della ricetta come parametro
   url = f"https://api.spoonacular.com/recipes/{recipe_id}/analyzedInstructions"#preparo l'url per fare la richiesta alla API esterna, inserendo l'id della ricetta che mi è stato passato come parametro
    params = {"apiKey": API_KEY}#preparo i parametri per la richiesta, la key
    response = requests.get(url, params=params)#faccio la richiesta alla API esterna con i parametri che ho preparato
    return response.json()#prendo i dati che mi ha restituito la API esterna e li trasformo in un formato che posso usare

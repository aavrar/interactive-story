# main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from core.proceduralEngine import ProceduralStoryEngine
import os
import requests
import difflib
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# Configure CORS
origins = [
    "https://interactive-story-zeta.vercel.app",  # Your Vercel domain
    "http://localhost:3000",  # For local development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

story_engine = ProceduralStoryEngine(templates_file="templates.json")

print(f"Templates loaded successfully: {len(story_engine.templates)} sections")
print(f"Available locations: {list(story_engine.templates['locations'].keys())}")

class CommandInput(BaseModel):
    command: str

class StartRunInput(BaseModel):
    seed: Optional[str] = None
    name: Optional[str] = None
    chosenClass: Optional[str] = None

class SaveGameInput(BaseModel):
    filename: Optional[str] = None

class LoadGameInput(BaseModel):
    filename: str

class IntentRequest(BaseModel):
    text: str

def smart_command_expand(user_input, choices):
    user_input = user_input.lower().strip()
    choices_lower = [c.lower() for c in choices]
    if user_input in choices_lower:
        return choices[choices_lower.index(user_input)]
    matches = difflib.get_close_matches(user_input, choices_lower, n=1, cutoff=0.7)
    if matches:
        return choices[choices_lower.index(matches[0])]
    for idx, choice in enumerate(choices_lower):
        if user_input in choice:
            return choices[idx]
    directions = {
        "n": "north", "s": "south", "e": "east", "w": "west",
        "ne": "northeast", "nw": "northwest", "se": "southeast", "sw": "southwest"
    }
    if user_input in directions:
        for idx, choice in enumerate(choices_lower):
            if f"go {directions[user_input]}" == choice or directions[user_input] in choice:
                return choices[idx]
    if user_input in directions.values():
        for idx, choice in enumerate(choices_lower):
            if f"go {user_input}" == choice or user_input in choice:
                return choices[idx]
    for idx, choice in enumerate(choices_lower):
        if choice.startswith("talk to ") and user_input in choice:
            return choices[idx]
    return user_input

@app.post("/start_new_run")
async def start_new_run_endpoint(input: StartRunInput):
    print("start_new_run_endpoint called")
    message = story_engine.start_new_run(input.seed)
    # Store player info in game state if provided
    if input.name is not None:
        story_engine.game_state.player_name = input.name
    if input.chosenClass is not None:
        story_engine.game_state.player_class = input.chosenClass
    return {"message": message}

@app.get("/scene")
async def get_scene_endpoint() -> Dict[str, Any]:
    try:
        scene_data = story_engine.get_current_scene_data()
        return scene_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/command")
async def process_command_endpoint(command: Dict[str, str]) -> Dict[str, str]:
    try:
        command_text = command["command"].strip()
        end_convo_keywords = ['bye', 'goodbye', 'leave', 'exit', 'end', 'farewell']
        scene_data = story_engine.get_current_scene_data()
        choices = scene_data.get("choices", [])
        user_input = command_text.lower()
        choices_lower = [c.lower() for c in choices]
        if story_engine.game_state.current_conversation and user_input in end_convo_keywords:
            expanded_command = command_text
        else:
            if user_input in choices_lower:
                expanded_command = choices[choices_lower.index(user_input)]
            else:
                found = False
                for idx, choice in enumerate(choices_lower):
                    if user_input in choice or choice in user_input:
                        expanded_command = choices[idx]
                        found = True
                        break
                    if any(token in choice.split() for token in user_input.split()):
                        expanded_command = choices[idx]
                        found = True
                        break
                if not found:
                    matches = difflib.get_close_matches(user_input, choices_lower, n=1, cutoff=0.7)
                    if matches:
                        expanded_command = choices[choices_lower.index(matches[0])]
                        found = True
                if not found and choices:
                    HUGGINGFACE_API_TOKEN = os.environ.get("HF_API_TOKEN")
                    MODEL = "facebook/bart-large-mnli"
                    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
                    payload = {
                        "inputs": command_text,
                        "parameters": {
                            "candidate_labels": choices
                        }
                    }
                    response = requests.post(
                        f"https://api-inference.huggingface.co/models/{MODEL}",
                        headers=headers,
                        json=payload
                    )
                    result = response.json()
                    if 'labels' in result and 'scores' in result and result['scores'][0] > 0.7:
                        expanded_command = result['labels'][0]
                    else:
                        expanded_command = command_text
        print(f"[{__import__('datetime').datetime.now()}] User input: '{command_text}' | Expanded to: '{expanded_command}'")
        if story_engine.game_state.current_conversation:
            result = story_engine.process_command(expanded_command)
            if story_engine.game_state.current_conversation:
                conversation_status = f" (Still talking to {story_engine.game_state.current_conversation.title()})"
            else:
                conversation_status = " (Conversation ended)"
            return {"result": result + conversation_status}
        else:
            result = story_engine.process_command(expanded_command)
            if story_engine.game_state.current_conversation:
                result += f" (Now talking to {story_engine.game_state.current_conversation.title()})"
            return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save")
async def save_game_endpoint(save_input: SaveGameInput = SaveGameInput()) -> Dict[str, str]:
    try:
        result = story_engine.save_run(save_input.filename)
        return {"status": "success", "message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/load")
async def load_game_endpoint(load_input: LoadGameInput) -> Dict[str, Any]:
    try:
        result = story_engine.load_run(load_input.filename)
        response = story_engine.get_current_scene_data()
        response['message'] = result
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/saves")
async def list_saves_endpoint() -> Dict[str, List[str]]:
    try:
        saves = story_engine.list_saves()
        return {"saves": saves}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status() -> Dict[str, Any]:
    try:
        if not story_engine.current_run:
            return {"status": "no_active_run", "message": "No active run. Start a new run first."}
        return {
            "status": "active",
            "seed": story_engine.current_run.seed,
            "current_location": story_engine.game_state.location,
            "visited_scenes": len(story_engine.current_run.visited_scenes),
            "inventory_count": len(story_engine.game_state.inventory)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inventory")
async def get_inventory() -> Dict[str, Any]:
    try:
        if not story_engine.current_run:
            raise HTTPException(status_code=400, detail="No active run")
        inventory_details = []
        for item_name, item in story_engine.game_state.inventory.items():
            inventory_details.append({
                "name": item.name,
                "description": item.description,
                "properties": item.properties
            })
        return {
            "inventory": inventory_details,
            "count": len(inventory_details)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/intent")
async def classify_intent(req: IntentRequest):
    HUGGINGFACE_API_TOKEN = os.environ.get("HF_API_TOKEN")
    MODEL = "facebook/bart-large-mnli"
    candidate_labels = ["move", "pickup", "talk", "inventory", "save", "load", "explore", "backtrack", "quit", "help"]
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
    payload = {
        "inputs": req.text,
        "parameters": {
            "candidate_labels": candidate_labels
        }
    }
    response = requests.post(
        f"https://api-inference.huggingface.co/models/{MODEL}",
        headers=headers,
        json=payload
    )
    result = response.json()
    intent = result['labels'][0] if 'labels' in result else "unknown"
    return {"intent": intent}

@app.get("/")
async def root():
    return {
        "message": "Procedural Story Engine API",
        "status": "running",
        "endpoints": [
            "/start_new_run",
            "/scene",
            "/command",
            "/save",
            "/load",
            "/saves",
            "/status",
            "/inventory"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

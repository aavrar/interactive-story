from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from core.engine import StoryEngine
import argparse
from core.proceduralEngine import ProceduralStoryEngine, ItemType, NPCType, GameState, Item
import os
import requests
import difflib
from dotenv import load_dotenv
load_dotenv()


app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

story_engine = ProceduralStoryEngine(templates_file="templates.json", enable_ai=True)

print(f"Templates loaded successfully: {len(story_engine.templates)} sections")
print(f"Available locations: {list(story_engine.templates['locations'].keys())}")

# Pydantic models for request/response
class CommandInput(BaseModel):
    command: str

class StartRunInput(BaseModel):
    seed: Optional[str] = None

class SaveGameInput(BaseModel):
    filename: Optional[str] = None

class LoadGameInput(BaseModel):
    filename: str

class IntentRequest(BaseModel):
    text: str



def smart_command_expand(user_input, choices):
    """
    Expands user input to the closest matching choice using fuzzy and token matching.
    """
    user_input = user_input.lower().strip()
    choices_lower = [c.lower() for c in choices]

    # 1. Exact match
    if user_input in choices_lower:
        return choices[choices_lower.index(user_input)]

    # 2. Fuzzy match (best match above a threshold)
    matches = difflib.get_close_matches(user_input, choices_lower, n=1, cutoff=0.7)
    if matches:
        return choices[choices_lower.index(matches[0])]

    # 3. Token match (e.g., "hermit" in "talk to cave hermit")
    for idx, choice in enumerate(choices_lower):
        if user_input in choice:
            return choices[idx]

    # 4. Special case: directions
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

    # 5. If user just types an NPC name, expand to "talk to [npc]"
    for idx, choice in enumerate(choices_lower):
        if choice.startswith("talk to ") and user_input in choice:
            return choices[idx]

    # 6. Fallback: return original input
    return user_input



@app.post("/start_new_run")
async def start_new_run_endpoint(seed: str = None) -> Dict[str, str]:
    """Starts a new procedural run."""
    print("start_new_run_endpoint called")  # Add this line
    message = story_engine.start_new_run(seed)
    return {"message": message}

@app.get("/scene")
async def get_scene_endpoint() -> Dict[str, Any]:
    """Gets the current scene data."""
    try:
        scene_data = story_engine.get_current_scene_data()
        return scene_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/command")
async def process_command_endpoint(command: Dict[str, str]) -> Dict[str, str]:
    """Processes a player command with hybrid expansion: alias/fuzzy first, zero-shot fallback."""
    try:
        import difflib

        command_text = command["command"].strip()
        end_convo_keywords = ['bye', 'goodbye', 'leave', 'exit', 'end', 'farewell']

        # Get available choices for the current scene
        scene_data = story_engine.get_current_scene_data()
        choices = scene_data.get("choices", [])

        user_input = command_text.lower()
        choices_lower = [c.lower() for c in choices]

        # 1. If in a conversation and the user types a conversation-ending keyword, do NOT expand
        if story_engine.game_state.current_conversation and user_input in end_convo_keywords:
            expanded_command = command_text

        else:
            # 2. Exact match
            if user_input in choices_lower:
                expanded_command = choices[choices_lower.index(user_input)]

            # 3. Token/alias match (substring or word match)
            else:
                found = False
                for idx, choice in enumerate(choices_lower):
                    # Substring match
                    if user_input in choice or choice in user_input:
                        expanded_command = choices[idx]
                        found = True
                        break
                    # Word match (e.g., "hermit" in "talk to cave hermit")
                    if any(token in choice.split() for token in user_input.split()):
                        expanded_command = choices[idx]
                        found = True
                        break

                # 4. Fuzzy match
                if not found:
                    matches = difflib.get_close_matches(user_input, choices_lower, n=1, cutoff=0.7)
                    if matches:
                        expanded_command = choices[choices_lower.index(matches[0])]
                        found = True

                # 5. Zero-shot fallback
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
                    # Only accept if confidence is high enough
                    if 'labels' in result and 'scores' in result and result['scores'][0] > 0.7:
                        expanded_command = result['labels'][0]
                    else:
                        expanded_command = command_text

        # Log the mapping
        print(f"[{__import__('datetime').datetime.now()}] User input: '{command_text}' | Expanded to: '{expanded_command}'")

        # Process as usual
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
    """Save the current game state."""
    try:
        result = story_engine.save_run(save_input.filename)
        return {"status": "success", "message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/load")
async def load_game_endpoint(load_input: LoadGameInput) -> Dict[str, Any]:
    """Load a saved game state."""
    try:
        result = story_engine.load_run(load_input.filename)
        response = story_engine.get_api_response()
        response['message'] = result
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/saves")
async def list_saves_endpoint() -> Dict[str, List[str]]:
    """List all available save files."""
    try:
        saves = story_engine.list_saves()
        return {"saves": saves}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Additional useful endpoints
@app.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get current game status and metadata."""
    try:
        if not story_engine.current_run:
            return {"status": "no_active_run", "message": "No active run. Start a new run first."}
        
        return {
            "status": "active",
            "seed": story_engine.current_run.seed,
            "current_location": story_engine.game_state.location,
            "visited_scenes": len(story_engine.current_run.visited_scenes),
            "inventory_count": len(story_engine.game_state.inventory),
            "has_ai": story_engine.enable_ai
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inventory")
async def get_inventory() -> Dict[str, Any]:
    """Get detailed inventory information."""
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
    # result['labels'] is a list ordered by confidence
    intent = result['labels'][0] if 'labels' in result else "unknown"
    return {"intent": intent}


# Root endpoint for API health check
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
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from core.engine import StoryEngine
import argparse
from core.proceduralEngine import ProceduralStoryEngine, ItemType, NPCType, GameState, Item

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
    """Processes a player command."""
    try:
        command_text = command["command"]
        result = story_engine.process_command(command_text)
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
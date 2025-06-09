from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from core.engine import StoryEngine
import argparse

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

story_engine = StoryEngine(story_file="story.json")

class CommandInput(BaseModel):
    command: str

@app.post("/command")
async def process_command_endpoint(command_input: CommandInput):
    """Endpoint to process a command and return the updated scene output."""
    try:
        message = story_engine.process_command(command_input.command)
        output = story_engine.get_scene_output()
        output['message'] = message  # Include the command processing message
        return output
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/scene")
async def get_scene_endpoint():
    """Endpoint to get the current scene output."""
    try:
        return story_engine.get_scene_output()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

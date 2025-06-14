# core/models.py

from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class Item(BaseModel):
    name: str
    description: str
    properties: Dict[str, Any]
    flags: List[str] = []

class Choice(BaseModel):
    action: str
    next_scene: str
    add_inventory: Optional[str] = None
    set_flag: Optional[str] = None
    condition: Optional[str] = None

class Scene(BaseModel):
    id: str
    descriptions: List[Dict[str, str]]
    items: List[Item] = []
    choices: List[Choice] = []
    flags: List[str] = []

class StoryMetadata(BaseModel):
    title: str
    author: str
    version: str

class StoryData(BaseModel):
    metadata: StoryMetadata
    scenes: List[Scene]

class GameState(BaseModel):
    location: str
    inventory: Dict[str, Item] = {}
    flags: List[str] = []
    current_conversation: Optional[str] = None
    player_name: Optional[str] = None
    player_class: Optional[str] = None

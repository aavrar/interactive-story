# core/proceduralEngine.py

import json
import random
import hashlib
from typing import Dict, Any, Optional, List, Set
from .models import Item, Choice, Scene, GameState

class ProceduralRun:
    def __init__(self, seed: str):
        self.seed = seed
        self.generated_scenes: Dict[str, Scene] = {}
        self.scene_connections: Dict[str, Dict[str, str]] = {}
        self.spawned_items: Dict[str, List[Item]] = {}
        self.spawned_npcs: Dict[str, List[dict]] = {}
        self.visited_scenes: Set[str] = set()
        self.location_history: List[str] = []

class ProceduralStoryEngine:
    def __init__(self, templates_file: str):
        self.templates = self.load_templates(templates_file)
        self.current_run: Optional[ProceduralRun] = None
        self.game_state = GameState(location="forest_clearing", inventory={}, flags=[])
        self.starting_location = self.templates["game_settings"]["starting_location"]

    def load_templates(self, templates_file: str) -> dict:
        with open(templates_file, 'r') as f:
            return json.load(f)

    def _generate_seed(self) -> str:
        import time
        return hashlib.md5(str(time.time()).encode()).hexdigest()[:8]

    def start_new_run(self, seed: str = None) -> str:
        if seed is None:
            seed = self._generate_seed()
        random.seed(seed)
        self.current_run = ProceduralRun(seed)
        self._generate_world()
        self.game_state = GameState(location=self.starting_location, inventory={}, flags=[])
        return f"Started new run with seed: {seed}"

    def _generate_world(self):
        locations = self.templates["locations"]
        items = self.templates["items"]
        npcs = self.templates["npcs"]

        for loc_id, loc_data in locations.items():
            # Items
            scene_items = []
            for item_id in loc_data.get("items", []):
                item_data = items.get(item_id)
                if item_data:
                    desc = item_data["description"]
                    if random.random() < 0.3:
                        desc += f" (It seems {random.choice(['unusually heavy', 'slightly magical', 'well-used', 'brand new'])}.)"
                    scene_items.append(Item(
                        name=item_data["name"],
                        description=desc,
                        properties=item_data["properties"]
                    ))
            self.current_run.spawned_items[loc_id] = scene_items

            # NPCs
            scene_npcs = []
            for npc_id in loc_data.get("npcs", []):
                npc_data = npcs.get(npc_id)
                if npc_data:
                    dialogue = dict(npc_data.get("dialogue", {}))
                    if "greeting" in dialogue:
                        dialogue["greeting"] += " " + random.choice([
                            "What brings you here?",
                            "You look like you have questions.",
                            "The forest is full of secrets.",
                            "Be wary of the shadows."
                        ])
                    if "quest" in dialogue and random.random() < 0.5:
                        dialogue["quest"] += " " + random.choice([
                            "Will you accept this challenge?",
                            "It's not for the faint of heart.",
                            "Legends say only the brave succeed."
                        ])
                    scene_npcs.append({
                        "name": npc_data["name"],
                        "description": npc_data["description"],
                        "personality": npc_data.get("personality", ""),
                        "dialogue": dialogue,
                        "quests": npc_data.get("quests", []),
                        "trades": npc_data.get("trades", {})
                    })
            self.current_run.spawned_npcs[loc_id] = scene_npcs

            # Scene object
            self.current_run.generated_scenes[loc_id] = Scene(
                id=loc_id,
                descriptions=[{"text": loc_data["description"]}],
                items=scene_items,
                choices=[]
            )

            # Connections
            self.current_run.scene_connections[loc_id] = dict(loc_data.get("connections", {}))

        # Ensure bidirectional connections
        for loc_id, conns in self.current_run.scene_connections.items():
            for direction, target in conns.items():
                if target in self.current_run.scene_connections:
                    reverse = self._reverse_direction(direction)
                    if reverse and loc_id not in self.current_run.scene_connections[target]:
                        self.current_run.scene_connections[target][reverse] = loc_id

    def _reverse_direction(self, direction: str) -> Optional[str]:
        opposites = {
            "north": "south", "south": "north",
            "east": "west", "west": "east",
            "up": "down", "down": "up",
            "northeast": "southwest", "southwest": "northeast",
            "northwest": "southeast", "southeast": "northwest",
            "deeper": "surface", "surface": "deeper",
            "inner": "outer", "outer": "inner",
            "secret": "secret", "portal": "portal",
            "tunnel": "tunnel", "shore": "shore",
            "passage": "passage", "shaft": "shaft",
            "deep": "shallow", "shallow": "deep"
        }
        return opposites.get(direction)

    def get_current_scene_data(self) -> Dict[str, Any]:
        if not self.current_run:
            return {"error": "No run active. Start a new run first."}
        current_location = self.game_state.location
        scene = self.current_run.generated_scenes.get(current_location)
        self.current_run.visited_scenes.add(current_location)
        if not self.current_run.location_history or self.current_run.location_history[-1] != current_location:
            self.current_run.location_history.append(current_location)
            if len(self.current_run.location_history) > 10:
                self.current_run.location_history = self.current_run.location_history[-10:]
        choices = []
        conns = self.current_run.scene_connections.get(current_location, {})
        for direction, target in conns.items():
            loc_name = self.templates["locations"][target]["name"]
            choices.append(f"go {direction} ({loc_name})")
        for item in self.current_run.spawned_items.get(current_location, []):
            choices.append(f"take {item.name.lower()}")
        for npc in self.current_run.spawned_npcs.get(current_location, []):
            choices.append(f"talk to {npc['name'].lower()}")
        return {
            "scene_id": current_location,
            "description": scene.descriptions[0]['text'] if scene and scene.descriptions else "You are somewhere unknown.",
            "items": [item.name for item in self.current_run.spawned_items.get(current_location, [])],
            "npcs": [npc["name"] for npc in self.current_run.spawned_npcs.get(current_location, [])],
            "choices": choices,
            "inventory": list(self.game_state.inventory.keys()),
            "seed": self.current_run.seed,
            "visited_scenes": len(self.current_run.visited_scenes),
            "current_conversation": getattr(self.game_state, "current_conversation", None)
        }

    def process_command(self, command: str) -> str:
        command = command.lower().strip()
        current_location = self.game_state.location

        # Movement
        if command.startswith("go "):
            parts = command.split()
            if len(parts) < 2:
                return "Go where?"
            direction = parts[1]
            conns = self.current_run.scene_connections.get(current_location, {})
            if direction in conns:
                self.game_state.location = conns[direction]
                return f"You go {direction} to {self.templates['locations'][conns[direction]]['name']}."
            return "You can't go that way."

        # Take item
        if command.startswith("take "):
            item_name = command[5:].strip().lower()
            items = self.current_run.spawned_items.get(current_location, [])
            for item in items:
                if item.name.lower() == item_name:
                    self.game_state.inventory[item.name] = item
                    items.remove(item)
                    return f"You take the {item.name}."
            return f"No {item_name} here to take."

        # Talk to NPC
        if command.startswith("talk to "):
            npc_name = command[8:].strip().lower()
            npcs = self.current_run.spawned_npcs.get(current_location, [])
            for npc in npcs:
                if npc["name"].lower() == npc_name:
                    self.game_state.current_conversation = npc["name"]
                    greeting = npc["dialogue"].get("greeting", "They greet you.")
                    return f"{npc['name']}: \"{greeting}\""
            return f"No {npc_name} here to talk to."

        # Inventory
        if command == "inventory":
            if not self.game_state.inventory:
                return "You aren't carrying anything."
            return "You are carrying: " + ", ".join(self.game_state.inventory.keys())

        # End conversation
        if command in ["bye", "goodbye", "leave", "exit", "end", "farewell"]:
            if getattr(self.game_state, "current_conversation", None):
                npc_name = self.game_state.current_conversation
                self.game_state.current_conversation = ""
                return f"You end your conversation with {npc_name}."
            return "You are not talking to anyone."

        return "I don't understand that command."

    def save_run(self, filename: str = None) -> str:
        import datetime
        if not self.current_run:
            return "No active run to save"
        if filename is None:
            now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"save_{now}.json"
        save_data = {
            "seed": self.current_run.seed,
            "game_state": {
                "location": self.game_state.location,
                "inventory": {k: v.dict() for k, v in self.game_state.inventory.items()},
                "flags": self.game_state.flags
            },
            "visited_scenes": list(self.current_run.visited_scenes)
        }
        with open(filename, 'w') as f:
            json.dump(save_data, f, indent=2)
        return f"Run saved to {filename}"

    def load_run(self, filename: str) -> str:
        try:
            with open(filename, 'r') as f:
                save_data = json.load(f)
            self.start_new_run(save_data["seed"])
            self.game_state.location = save_data["game_state"]["location"]
            self.game_state.flags = save_data["game_state"]["flags"]
            for item_name, item_data in save_data["game_state"]["inventory"].items():
                item = Item(**item_data)
                self.game_state.inventory[item_name] = item
            self.current_run.visited_scenes = set(save_data["visited_scenes"])
            return f"Run loaded from {filename}"
        except Exception as e:
            return f"Failed to load run: {e}"

    def list_saves(self) -> List[str]:
        import os
        save_files = []
        for file in os.listdir('.'):
            if file.startswith('save_') and file.endswith('.json'):
                save_files.append(file)
        return save_files

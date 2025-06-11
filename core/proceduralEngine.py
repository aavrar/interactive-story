import json
import random
import hashlib
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum
from transformers import pipeline
from .models import Item, Choice, Scene, StoryMetadata, StoryData, GameState
from nltk.tokenize import sent_tokenize

class ItemType(Enum):
    WEAPON = "weapon"
    POTION = "potion"
    ARMOR = "armor"
    KEY = "key"
    CONSUMABLE = "consumable"
    TOOL = "tool"

class NPCType(Enum):
    MERCHANT = "merchant"
    GUARD = "guard"
    HERMIT = "hermit"
    WANDERER = "wanderer"
    MYSTIC = "mystic"

@dataclass
class ItemTemplate:
    """Template for generating items with variations"""
    name_base: str
    item_type: ItemType
    description_template: str
    properties_range: Dict[str, tuple]  # e.g., {"damage": (10, 25)}
    rarity: float  # 0.0 to 1.0, lower = more rare
    scene_types: List[str]  # Which scene types this can appear in

@dataclass
class NPCTemplate:
    """Template for generating NPCs"""
    name_base: str
    npc_type: NPCType
    dialogue_templates: List[str]
    spawn_chance: float
    scene_types: List[str]
    interactions: List[str]  # e.g., ["trade", "quest", "info"]

@dataclass
class SceneTemplate:
    """Template for generating scene variations"""
    id: str
    base_description: str
    scene_type: str  # "forest", "cave", "castle", etc.
    possible_connections: List[str]  # Which scene types this can connect to
    max_connections: int
    item_spawn_chance: float
    npc_spawn_chance: float
    atmospheric_keywords: List[str]  # For AI generation context

@dataclass
class ProceduralRun:
    """Represents a complete run with its seed and generated content"""
    seed: str
    generated_scenes: Dict[str, Scene]
    scene_connections: Dict[str, List[str]]
    spawned_items: Dict[str, List[Item]]
    spawned_npcs: Dict[str, List[dict]]
    visited_scenes: Set[str] = field(default_factory=set)

class ProceduralStoryEngine:
    def __init__(self, templates_file: str, enable_ai: bool = True):
        self.templates = self.load_templates(templates_file)
        self.current_run: Optional[ProceduralRun] = None
        self.game_state = GameState(location="start", inventory={}, flags=[])
        
        # AI components
        self.enable_ai = enable_ai
        if enable_ai:
            try:
                self.narrative_pipeline = pipeline('text-generation', model='microsoft/DialoGPT-medium')
            except Exception as e:
                print(f"Failed to load AI model: {e}. Using rule-based generation.")
                self.enable_ai = False
        
        # Pre-defined content templates
        self.item_templates = self._initialize_item_templates()
        self.npc_templates = self._initialize_npc_templates()
        self.scene_templates = self._initialize_scene_templates()

    def _initialize_item_templates(self) -> List[ItemTemplate]:
        """Initialize item generation templates"""
        return [
            ItemTemplate("Sword", ItemType.WEAPON, "A {adjective} sword that gleams in the light", 
                        {"damage": (15, 30)}, 0.3, ["forest", "castle", "ruins"]),
            ItemTemplate("Health Potion", ItemType.POTION, "A {color} potion that bubbles gently", 
                        {"heal": (20, 50)}, 0.6, ["forest", "cave", "ruins"]),
            ItemTemplate("Leather Armor", ItemType.ARMOR, "{quality} leather armor with metal studs", 
                        {"defense": (5, 15)}, 0.4, ["forest", "castle"]),
            ItemTemplate("Ancient Key", ItemType.KEY, "An ornate key covered in {material}", 
                        {}, 0.1, ["ruins", "castle", "cave"]),
            ItemTemplate("Magic Ring", ItemType.CONSUMABLE, "A ring that {effect} when worn", 
                        {"magic": (10, 25)}, 0.2, ["ruins", "cave"])
        ]

    def _initialize_npc_templates(self) -> List[NPCTemplate]:
        """Initialize NPC generation templates"""
        return [
            NPCTemplate("Merchant", NPCType.MERCHANT, 
                       ["Looking to buy or sell something?", "I have rare wares from distant lands!"],
                       0.3, ["forest", "castle"], ["trade", "info"]),
            NPCTemplate("Hermit", NPCType.HERMIT,
                       ["Few venture this deep into the wilderness...", "I know secrets of these lands."],
                       0.2, ["forest", "cave"], ["info", "quest"]),
            NPCTemplate("Guard", NPCType.GUARD,
                       ["Halt! State your business.", "These are dangerous times, traveler."],
                       0.4, ["castle", "ruins"], ["info", "challenge"]),
            NPCTemplate("Mystic", NPCType.MYSTIC,
                       ["The spirits whisper of your coming...", "Your destiny is clouded but not sealed."],
                       0.15, ["ruins", "cave"], ["prophecy", "magic"])
        ]

    def _initialize_scene_templates(self) -> List[SceneTemplate]:
        """Initialize scene generation templates"""
        return [
            SceneTemplate("forest_clearing", "A peaceful clearing surrounded by ancient trees",
                         "forest", ["forest_path", "cave_entrance", "ruins"], 3, 0.7, 0.3,
                         ["sunlight", "birds", "leaves", "peaceful"]),
            SceneTemplate("dark_cave", "A mysterious cave with echoing depths",
                         "cave", ["cave_chamber", "underground_river", "forest_clearing"], 2, 0.5, 0.4,
                         ["darkness", "echoes", "damp", "mysterious"]),
            SceneTemplate("ancient_ruins", "Crumbling stone structures overgrown with vines",
                         "ruins", ["ruins_chamber", "castle_gate", "forest_path"], 3, 0.6, 0.5,
                         ["ancient", "crumbling", "mysterious", "overgrown"]),
            SceneTemplate("castle_courtyard", "A grand courtyard with weathered stone walls",
                         "castle", ["castle_hall", "castle_tower", "forest_path"], 3, 0.4, 0.6,
                         ["grand", "imposing", "weathered", "regal"])
        ]

    def start_new_run(self, seed: str = None) -> str:
        """Start a new procedural run with the given seed"""
        if seed is None:
            seed = self._generate_seed()
        
        # Set random seed for reproducibility
        random.seed(seed)
        
        # Generate the procedural content
        self.current_run = self._generate_run(seed)
        
        # Get the actual starting location from the templates
        starting_location = self.templates['game_settings']['starting_location']
        
        # Reset game state with the correct starting location
        self.game_state = GameState(location=starting_location, inventory={}, flags=[])
        
        return f"Started new run with seed: {seed}"

    def _generate_seed(self) -> str:
        """Generate a unique seed for this run"""
        import time
        return hashlib.md5(str(time.time()).encode()).hexdigest()[:8]

    def _generate_run(self, seed: str) -> ProceduralRun:
        """Generate all content for this run based on the seed"""
        run = ProceduralRun(seed=seed, generated_scenes={}, scene_connections={}, 
                            spawned_items={}, spawned_npcs={})
    
        # Generate ALL scenes from templates.json instead of just a network
        for location_id in self.templates['locations'].keys():
            # Find matching template or use a default one
            template = None
            for scene_template in self.scene_templates:
                if scene_template.scene_type in location_id or location_id.startswith(scene_template.scene_type):
                    template = scene_template
                    break
        
            # If no matching template found, use forest_clearing as default
            if not template:
                template = self.scene_templates[0]  # forest_clearing
        
            # Create scene from template
            scene = self._create_scene_from_template(template, location_id)
            run.generated_scenes[location_id] = scene

        print(f"Generated scenes: {list(run.generated_scenes.keys())}")  # Debugging line
    
        # Generate items for each scene
        for scene_id in run.generated_scenes.keys():
            run.spawned_items[scene_id] = self._generate_scene_items(scene_id, run)
    
        # Generate NPCs for each scene
        for scene_id in run.generated_scenes.keys():
            run.spawned_npcs[scene_id] = self._generate_scene_npcs(scene_id, run)
    
        return run
    
    def _get_scene_template_for_location(self, location_id: str) -> 'SceneTemplate':
        """Get appropriate scene template for a location ID"""
        # Try to match by scene type keywords
        location_lower = location_id.lower()
    
        if any(word in location_lower for word in ['forest', 'grove', 'clearing', 'tree']):
            return next(t for t in self.scene_templates if t.scene_type == 'forest')
        elif any(word in location_lower for word in ['cave', 'cavern', 'underground']):
            return next(t for t in self.scene_templates if t.scene_type == 'cave')
        elif any(word in location_lower for word in ['ruin', 'ancient', 'stone']):
            return next(t for t in self.scene_templates if t.scene_type == 'ruins')
        elif any(word in location_lower for word in ['castle', 'tower', 'hall', 'courtyard']):
            return next(t for t in self.scene_templates if t.scene_type == 'castle')
    
        # Default to forest template
        return self.scene_templates[0]

    def _generate_scene_network(self, run: ProceduralRun, template: SceneTemplate, 
                                scene_id: str, depth: int, max_depth: int, parent_id: str = None):
        """Recursively generate connected scenes"""
        if depth >= max_depth:
            return
        
        # Generate base scene with the provided scene_id
        scene = self._create_scene_from_template(template, scene_id)
        run.generated_scenes[scene_id] = scene
        
        # Load connections from templates.json if available
        connections_from_template = []
        if scene_id in self.templates['locations'] and 'connections' in self.templates['locations'][scene_id]:
            connections_from_template = list(self.templates['locations'][scene_id]['connections'].values())
        
        run.scene_connections[scene_id] = connections_from_template
        
        # Generate additional connections if needed
        num_connections = random.randint(1, min(template.max_connections, 3))
        
        for i in range(num_connections):
            # Choose a random scene type to connect to
            if template.possible_connections:
                target_type = random.choice(template.possible_connections)
                target_template = next((t for t in self.scene_templates if t.scene_type == target_type), None)
                
                if target_template:
                    child_id = target_template.id
                    if child_id not in run.scene_connections[scene_id] and child_id not in run.generated_scenes:
                        run.scene_connections[scene_id].append(child_id)
                        
                        # Recursively generate child scene
                        self._generate_scene_network(run, target_template, child_id, depth+1, max_depth, scene_id)

    def _create_scene_from_template(self, template: SceneTemplate, scene_id: str) -> Scene:
        """Create a scene from a template with AI-enhanced description"""
        # Use description from templates.json if available, otherwise use base description
        if scene_id in self.templates['locations']:
            description = self.templates['locations'][scene_id]['description']
        else:
            description = template.base_description

        # Generate enhanced description using the template's base description as fallback
        base_desc = description if description else template.base_description
    
        if self.enable_ai:
            enhanced_desc = self._generate_enhanced_description(template)
        else:
            enhanced_desc = self._generate_rule_based_description(template)
    
        # If enhancement failed, use the original description
        if not enhanced_desc or enhanced_desc == template.base_description:
            enhanced_desc = base_desc
    
        # Create choices (will be populated dynamically based on connections)
        choices = []
    
        # Create scene
        return Scene(
            id=scene_id,
            descriptions=[{"text": enhanced_desc}],
            items=[],  # Will be populated by _generate_scene_items
            choices=choices
        )

    def _generate_enhanced_description(self, template: SceneTemplate) -> str:
        """Use AI to enhance scene descriptions"""
        keywords = ", ".join(template.atmospheric_keywords[:3])
        prompt = f"{template.base_description} The atmosphere is {keywords}. You also notice"
        
        try:
            generated = self.narrative_pipeline(
                prompt,
                max_new_tokens=20,
                do_sample=True,
                temperature=0.7,
                top_p=0.8,
                pad_token_id=self.narrative_pipeline.tokenizer.eos_token_id
            )
            
            full_text = generated[0]['generated_text']
            continuation = full_text[len(prompt):].strip()
            
            if continuation:
                sentences = sent_tokenize(continuation)
                if sentences:
                    addition = sentences[0].strip()
                    if len(addition) > 5 and len(addition.split()) <= 15:
                        return f"{template.base_description} {addition}"
            
        except Exception as e:
            print(f"AI generation failed: {e}")
        
        return template.base_description

    def _generate_rule_based_description(self, template: SceneTemplate) -> str:
        """Generate enhanced descriptions using rules"""
        atmospheric_additions = {
            "forest": ["Sunlight filters through the canopy above.", "The scent of pine fills the air.", 
                      "Birds chirp in the distance."],
            "cave": ["Water drips somewhere in the darkness.", "Cool air flows from deeper chambers.", 
                    "Your footsteps echo off stone walls."],
            "ruins": ["Vines creep over ancient stonework.", "Time has weathered these walls.", 
                     "Shadows hide forgotten secrets."],
            "castle": ["Banners flutter in the breeze.", "The stone feels cold to the touch.", 
                      "Echoes of past glory linger here."]
        }
        
        additions = atmospheric_additions.get(template.scene_type, ["The air feels different here."])
        chosen_addition = random.choice(additions)
        
        return f"{template.base_description} {chosen_addition}"

    def _generate_scene_items(self, scene_id: str, run: ProceduralRun) -> List[Item]:
        """Generate items for a specific scene"""
        items = []
    
        # Get the list of item IDs for this scene from templates.json
        location_data = self.templates['locations'].get(scene_id)
        if location_data and 'items' in location_data:
            item_ids = location_data['items']
        
            # Load item data from templates.json and create Item objects
            for item_id in item_ids:
                item_data = self.templates['items'].get(item_id)
                if item_data:
                    item = Item(
                        name=item_data['name'],
                        description=item_data['description'],
                        properties=item_data['properties']
                    )
                    items.append(item)
        # If no location data exists, return empty list (no items)
    
        return items

    def _create_item_from_template(self, template: ItemTemplate) -> Item:
        """Create an item instance from a template"""
        # Generate random properties
        properties = {}
        for prop, (min_val, max_val) in template.properties_range.items():
            properties[prop] = random.randint(min_val, max_val)
        
        # Generate descriptive variations
        descriptors = {
            "adjective": random.choice(["sharp", "gleaming", "ancient", "mysterious", "ornate"]),
            "color": random.choice(["crimson", "azure", "emerald", "golden", "silver"]),
            "quality": random.choice(["worn", "fine", "masterwork", "crude", "elegant"]),
            "material": random.choice(["runes", "patina", "engravings", "jewels", "scratches"]),
            "effect": random.choice(["glows softly", "feels warm", "hums with power", "shimmers"])
        }
        
        description = template.description_template.format(**descriptors)
        
        return Item(
            name=template.name_base,
            description=description,
            properties=properties
        )

    def _generate_scene_npcs(self, scene_id: str, run: ProceduralRun) -> List[dict]:
        """Generate NPCs for a specific scene"""
        npcs = []

        # Get the list of NPC IDs for this scene from templates.json
        location_data = self.templates['locations'].get(scene_id)
        if location_data and 'npcs' in location_data:
            npc_ids = location_data['npcs']
            for npc_id in npc_ids:
                npc_data = self.templates['npcs'].get(npc_id)
                if npc_data:
                    npcs.append(npc_data)
        # If no location data exists, return empty list (no NPCs)

        return npcs

    def _get_scene_type_from_id(self, scene_id: str) -> str:
        """Extract scene type from scene ID"""
        if scene_id == "start":
            return "forest"
        return scene_id.split("_")[0]

    def get_current_scene_data(self) -> Dict[str, Any]:
        """Get current scene with all procedurally generated content"""
        if not self.current_run:
            return {"error": "No run active. Start a new run first."}
    
        current_location = self.game_state.location
        print(f"Current location: {current_location}")  # Debugging line
        print(f"Available scenes: {list(self.current_run.generated_scenes.keys())}")  # Debugging line

        if 'locations' not in self.templates:
            print("Error: 'locations' key not found in templates")
            return {"error": "Missing 'locations' data in templates"}
    
        scene = self.current_run.generated_scenes.get(current_location)
    
        if not scene:
            print(f"Error: Scene {current_location} not found in generated scenes")
            return {"error": f"Scene {current_location} not found"}
    
        # Mark scene as visited and track location history
        self.current_run.visited_scenes.add(current_location)
        if not hasattr(self.current_run, 'location_history'):
            self.current_run.location_history = []
    
        if not self.current_run.location_history or self.current_run.location_history[-1] != current_location:
            self.current_run.location_history.append(current_location)
            # Keep history manageable
            if len(self.current_run.location_history) > 10:
                self.current_run.location_history = self.current_run.location_history[-10:]
    
        # Get connections from templates.json (if it exists)
        location_data = self.templates['locations'].get(current_location)
    
        connections = []
        if location_data and 'connections' in location_data:
            connections = list(location_data['connections'].keys())  # Get the directions (north, south, etc.)
    
        # Create movement choices
        choices = []
        for direction in connections[:4]:  # Max 4 connections
            choices.append(f"go {direction}")
    
        # If no predefined connections or very few, add exploration options
        if len(connections) < 2:
            exploration_options = self._generate_exploration_options(current_location)
            for direction, new_location in exploration_options:
                choices.append(f"explore {direction}")
    
        # Add backtrack options
        backtrack_options = self._get_backtrack_options()
        choices.extend(backtrack_options)
    
        # Get items and NPCs for this scene
        scene_items = self.current_run.spawned_items.get(current_location, [])
        scene_npcs = self.current_run.spawned_npcs.get(current_location, [])
        
        # Debugging: Print the scene_npcs list
        print(f"Scene NPCs: {scene_npcs}")
    
        # Add NPC interaction choices
        if not self.game_state.current_conversation:
            for npc in scene_npcs:
                choices.append(f"talk to {npc['name'].lower()}")
        else:
            choices.append("say bye (to end conversation)")
    
        # Get the scene description - first try templates.json, then fall back to generated scene
        description = "You are in an unknown location."
        if location_data and 'description' in location_data:
            description = location_data['description']
        elif scene and scene.descriptions:
            description = scene.descriptions[0]['text']
    
        return {
            "scene_id": current_location,
            "description": description,
            "items": [item.name for item in scene_items],
            "npcs": [npc["name"] for npc in scene_npcs],
            "choices": choices,
            "inventory": list(self.game_state.inventory.keys()),
            "seed": self.current_run.seed,
            "visited_scenes": len(self.current_run.visited_scenes),
            "current_conversation": self.game_state.current_conversation.title() if self.game_state.current_conversation else None
        }

    def process_command(self, command: str) -> str:
        """Process player commands in the procedural world"""
        if not self.current_run:
            return "No run active. Use 'start new run' to begin."
        
        command = command.lower().strip()
        current_location = self.game_state.location
        
        # Handle movement
        if command.startswith("go "):
            return self._handle_movement(command)
        
        if command.startswith("backtrack to "):
            return self._handle_movement(command)
        
        if command.startswith("explore "):
            return self._handle_movement(command)
        
        # Handle item interactions
        elif command.startswith("take "):
            return self._handle_take_item(command)
        
        # Handle NPC interactions and conversations
        elif command.startswith("talk to ") or self.game_state.current_conversation:
            return self._handle_npc_interaction(command)
        
        # Standard inventory commands
        elif command == "inventory":
            if not self.game_state.inventory:
                return "You aren't carrying anything."
            return f"You are carrying: {', '.join(self.game_state.inventory.keys())}"
        
        else:
            return "I don't understand that command. Try 'go [direction]', 'take [item]', or 'talk to [npc]'"

    def _handle_movement(self, command: str) -> str:
        """Handle movement between scenes"""
        command_parts = command.split()
    
        if len(command_parts) < 2:
            return "Please specify a direction to go."
    
        current_location = self.game_state.location
    
        # Handle backtracking
        if command.startswith("backtrack to "):
            target_name = command[13:].strip().lower().replace(' ', '_')
        
            # Find matching location in history
            if hasattr(self.current_run, 'location_history'):
                for location in self.current_run.location_history:
                    if location.lower() == target_name:
                        self.game_state.location = location
                        return f"You backtrack to {location.replace('_', ' ').title()}."
        
            return "You can't backtrack there."
    
        # Handle exploration
        elif command.startswith("explore "):
            direction = command[8:].strip()
        
            # Generate new location based on exploration options
            exploration_options = self._generate_exploration_options(current_location)
        
            for exp_direction, new_location in exploration_options:
                if exp_direction == direction:
                    # Generate the new scene if it doesn't exist
                    if new_location not in self.current_run.generated_scenes:
                        self._generate_missing_scene(new_location)
                
                    self.game_state.location = new_location
                    return f"You explore {direction} and discover {new_location.replace('_', ' ').title()}."
        
            return "You can't explore in that direction."
    
        # Handle regular movement
        elif command.startswith("go "):
            direction = command[3:].strip()
        
            # Get connections and directions from templates.json
            location_data = self.templates['locations'].get(current_location)
            if not location_data or 'connections' not in location_data:
                return "You can't go that way."
        
            connections = location_data['connections']
        
            # Check if the requested direction is a valid connection
            if direction in connections:
                new_location = connections[direction]
            
                # Check if the target scene exists in generated scenes
                if new_location not in self.current_run.generated_scenes:
                    # Generate the missing scene on-the-fly
                    self._generate_missing_scene(new_location)
            
                self.game_state.location = new_location
                return f"You head {direction}."
        
            return "You can't go that way."
    
        return "I don't understand that movement command."
    
    def _generate_missing_scene(self, scene_id: str):
        """Generate a missing scene on-the-fly"""
        # Check if scene data exists in templates
        if scene_id in self.templates['locations']:
            # Use existing template data
            template = self._get_scene_template_for_location(scene_id)
            scene = self._create_scene_from_template(template, scene_id)
        else:
            # Create a generic scene for unknown locations
            template = self.scene_templates[0]  # Use forest as default
            generic_description = f"You find yourself in {scene_id.replace('_', ' ').title()}. This area seems unexplored and mysterious."
        
            scene = Scene(
                id=scene_id,
                descriptions=[{"text": generic_description}],
                items=[],
                choices=[]
            )
    
        # Add to current run
        self.current_run.generated_scenes[scene_id] = scene
        self.current_run.spawned_items[scene_id] = self._generate_scene_items(scene_id, self.current_run)
        self.current_run.spawned_npcs[scene_id] = self._generate_scene_npcs(scene_id, self.current_run)
    
        print(f"Generated missing scene: {scene_id}")

    def _generate_exploration_options(self, scene_id: str) -> List[str]:
        """Generate procedural exploration options for scenes with no predefined connections"""
        directions = ["north", "south", "east", "west", "northeast", "northwest", "southeast", "southwest"]
        terrain_types = ["forest", "cave", "ruins", "castle", "village", "mountain", "river", "field"]
    
        # Get context from visited scenes to influence generation
        visited_terrain = set()
        for visited_id in self.current_run.visited_scenes:
            for terrain in terrain_types:
                if terrain in visited_id.lower():
                    visited_terrain.add(terrain)
    
        # Generate 2-4 exploration options based on current scene context
        options = []
        scene_lower = scene_id.lower()
    
        # Determine base terrain type
        current_terrain = "unknown"
        for terrain in terrain_types:
            if terrain in scene_lower:
                current_terrain = terrain
                break
    
        # Generate contextual exploration options
        available_directions = random.sample(directions, random.randint(2, 4))
    
        for direction in available_directions:
            # Choose terrain based on current location and what's been visited
            if current_terrain == "forest":
                possible_terrains = ["forest", "cave", "ruins", "village"]
            elif current_terrain == "cave":
                possible_terrains = ["cave", "underground", "ruins"]
            elif current_terrain == "village" or "farm" in scene_lower:
                possible_terrains = ["field", "forest", "village", "river"]
            else:
                possible_terrains = terrain_types
        
            # Bias towards unvisited terrain types
            unvisited_terrains = [t for t in possible_terrains if t not in visited_terrain]
            if unvisited_terrains:
                chosen_terrain = random.choice(unvisited_terrains)
            else:
                chosen_terrain = random.choice(possible_terrains)
        
            # Generate location name
            terrain_descriptors = {
                "forest": ["grove", "clearing", "thicket", "woods"],
                "cave": ["cavern", "grotto", "tunnel", "chamber"],
                "ruins": ["ruins", "stones", "temple", "monument"],
                "village": ["hamlet", "settlement", "village", "outpost"],
                "field": ["meadow", "plains", "farmland", "pasture"],
                "river": ["stream", "brook", "crossing", "bridge"],
                "mountain": ["peak", "ridge", "slope", "cliff"]
            }
        
            descriptors = terrain_descriptors.get(chosen_terrain, ["area", "region", "location"])
            descriptor = random.choice(descriptors)
        
            # Add some variety with adjectives
            adjectives = ["hidden", "ancient", "mysterious", "forgotten", "distant", "peaceful", "dark", "secluded"]
            if random.random() < 0.6:  # 60% chance to add adjective
                adjective = random.choice(adjectives)
                new_location = f"{adjective}_{descriptor}"
            else:
                new_location = f"wild_{descriptor}"
        
            options.append((direction, new_location))
    
        return options
    
    def _get_backtrack_options(self) -> List[str]:
        """Get available backtrack options based on movement history"""
        if not hasattr(self.current_run, 'location_history'):
            self.current_run.location_history = []
    
        # Get last few locations (excluding current)
        recent_locations = []
        current_location = self.game_state.location
    
        for location in reversed(self.current_run.location_history):
            if location != current_location and location not in recent_locations:
                recent_locations.append(location)
                if len(recent_locations) >= 3:  # Max 3 backtrack options
                    break
    
        backtrack_choices = []
        for i, location in enumerate(recent_locations):
            choice_text = f"backtrack to {location.replace('_', ' ').title()}"
            backtrack_choices.append(choice_text)
    
        return backtrack_choices

    def _handle_take_item(self, command: str) -> str:
        """Handle taking items"""
        item_name = command[5:].strip()
        current_location = self.game_state.location
        scene_items = self.current_run.spawned_items.get(current_location, [])
        
        for item in scene_items:
            if item.name.lower() == item_name:
                self.game_state.inventory[item.name] = item
                scene_items.remove(item)
                return f"You took the {item.name}."
        
        return f"There's no {item_name} here."

    def _handle_npc_interaction(self, command: str) -> str:
        """Handle NPC interactions with enhanced dialogue system"""
        current_location = self.game_state.location
        scene_npcs = self.current_run.spawned_npcs.get(current_location, [])

        # Check if already in a conversation
        if self.game_state.current_conversation:
            return self._handle_conversation_response(command, scene_npcs)
    
        # Start a new conversation
        else:
            return self._start_conversation(command, scene_npcs)

    def _start_conversation(self, command: str, scene_npcs: list) -> str:
        """Start a new conversation with an NPC"""
        npc_name = command[8:].strip()  # Remove "talk to "
        print(f"Command in _start_conversation: {command}")

        for npc in scene_npcs:
            if npc["name"].lower() == npc_name:
                self.game_state.current_conversation = npc["name"].lower()

                # Debugging: Print the NPC data
                print(f"NPC data: {npc}")
                print(f"Type of NPC data: {type(npc)}")

                # Get greeting from NPC data
                dialogue = npc.get("dialogue")
                if isinstance(dialogue, dict):
                    greeting = dialogue.get("greeting", "Hello there, traveler.")
                else:
                    greeting = "Hello there, traveler."  # Default greeting if dialogue is not a dict

                # Generate conversation options
                options = self._get_conversation_options(npc)
                options_text = "\n".join([f"- {option}" for option in options])

                return (f'{npc["name"]}: "{greeting}"\n\n'
                    f'What would you like to say?\n{options_text}\n'
                    f'(Or say "bye" to end the conversation)')

        return f"There's no {npc_name} here to talk to."

    def _handle_conversation_response(self, command: str, scene_npcs: list) -> str:
        """Handle responses during an active conversation"""
        command = command.lower().strip()

        # Debugging: Print the scene_npcs and the result of _get_current_npc
        print(f"Scene NPCs: {scene_npcs}")
        npc = self._get_current_npc(scene_npcs)
        print(f"Current NPC: {npc}")

        # Handle ending conversation
        if command in ['bye', 'goodbye', 'leave', 'exit', 'end', 'farewell']:
            npc_name = self.game_state.current_conversation
            npc = self._get_current_npc(scene_npcs)

            if npc:
                dialogue = npc.get("dialogue")
                if isinstance(dialogue, dict):
                    farewell = dialogue.get("farewell", "Safe travels, adventurer.")
                else:
                    farewell = "Safe travels, adventurer."
                self.game_state.current_conversation = None
                return f'{npc["name"]}: "{farewell}"'
            else:
                self.game_state.current_conversation = None
                return "You end the conversation."

        # Handle specific dialogue options
        npc = self._get_current_npc(scene_npcs)
        if not npc:
            self.game_state.current_conversation = None
            return "That NPC is no longer here."

        # Process different dialogue types
        if command in ['quest', 'ask about quest', 'do you have any quests']:
            dialogue = npc.get("dialogue")
            if isinstance(dialogue, dict):
                quest_dialogue = dialogue.get("quest", "I don't have any tasks for you right now.")
            else:
                quest_dialogue = "I don't have any tasks for you right now."
            return f'{npc["name"]}: "{quest_dialogue}"'

        elif command in ['trade', 'shop', 'buy', 'sell']:
            return self._handle_trade_interaction(npc)

        elif command in ['info', 'information', 'tell me about this place']:
            return self._handle_info_request(npc)

        else:
            # Generate contextual response based on NPC personality
            return self._generate_contextual_reply(npc, command)

    def _get_current_npc(self, scene_npcs: list) -> dict:
        """Get the NPC currently being talked to"""
        if not self.game_state.current_conversation:
            return None
    
        return next((npc for npc in scene_npcs 
                    if npc["name"].lower() == self.game_state.current_conversation), None)

    def _get_conversation_options(self, npc: dict) -> list:
        """Generate available conversation options for an NPC"""
        options = []
    
        # Check if NPC has quests
        if npc.get("quests") or npc.get("dialogue", {}).get("quest"):
            options.append("Ask about quests")
    
        # Check if NPC can trade
        if npc.get("trades") or "merchant" in npc.get("name", "").lower():
            options.append("Trade")
    
        # Always available options
        options.extend(["Ask for information", "Just chat"])
    
        return options

    def _handle_trade_interaction(self, npc: dict) -> str:
        """Handle trading with NPCs"""
        trades = npc.get("trades", {})
    
        if not trades:
            return f'{npc["name"]}: "I don\'t have anything to trade right now."'
    
        # For now, just acknowledge trade request
        return f'{npc["name"]}: "I have some items for trade, but my inventory system is being updated."'

    def _handle_info_request(self, npc: dict) -> str:
        """Handle information requests from NPCs"""
        # Generate info based on NPC personality and location
        personality = npc.get("personality", "friendly")
    
        info_responses = {
            "friendly": "This is a peaceful place, though I've heard strange rumors lately.",
            "gruff": "Not much to say about this place. Keep your wits about you.",
            "mysterious": "There are secrets here that few understand...",
            "wise": "This land holds many stories, if you know how to listen.",
            "cheerful": "Oh, this is a wonderful area! So much to explore!"
        }
    
        response = info_responses.get(personality, "I don't know much about this place.")
        return f'{npc["name"]}: "{response}"'

    def _generate_contextual_reply(self, npc: dict, player_input: str) -> str:
        """Generate contextual replies based on NPC personality and player input"""
        personality = npc.get("personality", "neutral")
    
        # Personality-based response patterns
        response_patterns = {
            "friendly": [
                "That's interesting! Tell me more.",
                "I appreciate you sharing that with me.",
                "You seem like a good person to talk to."
            ],
            "gruff": [
                "Hmph. If you say so.",
                "I suppose that's one way to look at it.",
                "Not much more to add to that."
            ],
            "mysterious": [
                "There is more to that than meets the eye...",
                "Your words carry deeper meaning.",
                "I sense there is something you're not telling me."
            ],
            "wise": [
                "Wisdom often comes from unexpected places.",
                "Your observation shows insight.",
                "There is truth in what you say."
            ],
            "cheerful": [
                "How delightful!",
                "That's wonderful to hear!",
                "You've brightened my day!"
            ]
        }
    
        patterns = response_patterns.get(personality, [
            "I see.",
            "That's interesting.",
            "Tell me more."
        ])
    
        response = random.choice(patterns)
        return f'{npc["name"]}: "{response}"'

    def load_templates(self, templates_file: str) -> dict:
        """Load template configuration from JSON file"""
        try:
            with open(templates_file, 'r') as f:
                templates = json.load(f)
            return templates
        except FileNotFoundError:
            print(f"Error: Templates file not found: {templates_file}")
            return {}
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in templates file: {templates_file}")
            return {}

    def save_run(self, filename: str = None) -> str:
        """Save current procedural run to file"""
        if not self.current_run:
            return "No active run to save"
    
        if filename is None:
            filename = f"save_{self.current_run.seed}.json"
    
        save_data = {
            "seed": self.current_run.seed,
            "game_state": {
                "location": self.game_state.location,
                "inventory": {k: {"name": v.name, "description": v.description, "properties": v.properties} 
                            for k, v in self.game_state.inventory.items()},
                "flags": self.game_state.flags
            },
            "visited_scenes": list(self.current_run.visited_scenes)
        }
    
        with open(filename, 'w') as f:
            json.dump(save_data, f, indent=2)
    
        return f"Run saved to {filename}"

    def load_run(self, filename: str) -> str:
        """Load a saved procedural run"""
        try:
            with open(filename, 'r') as f:
                save_data = json.load(f)
        
            # Regenerate the run with the same seed
            self.start_new_run(save_data["seed"])
        
            # Restore game state
            self.game_state.location = save_data["game_state"]["location"]
            self.game_state.flags = save_data["game_state"]["flags"]
        
            # Restore inventory
            for item_name, item_data in save_data["game_state"]["inventory"].items():
                item = Item(
                    name=item_data["name"],
                    description=item_data["description"],
                    properties=item_data["properties"]
                )
                self.game_state.inventory[item_name] = item
        
            # Restore visited scenes
            self.current_run.visited_scenes = set(save_data["visited_scenes"])
        
            return f"Run loaded from {filename}"
    
        except Exception as e:
            return f"Failed to load run: {e}"

    def get_api_response(self) -> Dict[str, Any]:
        """Get formatted response for API/frontend"""
        scene_data = self.get_current_scene_data()
    
        if "error" in scene_data:
            return {"status": "error", "message": scene_data["error"]}
    
        return {
            "status": "success",
            "data": {
                "scene": {
                    "id": scene_data["scene_id"],
                    "description": scene_data["description"],
                    "items": scene_data["items"],
                    "npcs": scene_data["npcs"]
                },
                "player": {
                    "location": self.game_state.location,
                    "inventory": scene_data["inventory"]
                },
                "choices": scene_data["choices"],
                "meta": {
                    "seed": scene_data["seed"],
                    "visited_count": scene_data["visited_scenes"]
                }
            }
        }

    def list_saves(self) -> List[str]:
        """List all available save files"""
        import os
        save_files = []
        for file in os.listdir('.'):
            if file.startswith('save_') and file.endswith('.json'):
                save_files.append(file)
        return save_files

    def process_command_with_save(self, command: str) -> str:
        """Extended command processor with save/load functionality"""
        command = command.lower().strip()
    
        # Handle save commands
        if command == "save":
            return self.save_run()
        elif command.startswith("save "):
            filename = command[5:].strip()
            if not filename.endswith('.json'):
                filename += '.json'
            return self.save_run(filename)
    
        # Handle load commands
        elif command.startswith("load "):
            filename = command[5:].strip()
            if not filename.endswith('.json'):
                filename += '.json'
            return self.load_run(filename)
    
        # Handle list saves
        elif command == "list saves":
            saves = self.list_saves()
            if saves:
                return f"Available saves: {', '.join(saves)}"
            else:
                return "No save files found."
    
        # Fall back to original command processing
        else:
            return self.process_command(command)
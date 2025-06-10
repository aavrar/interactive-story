import json
import os
from typing import Dict, Any, Optional, List
from transformers import pipeline
from .models import Item, Choice, Scene, StoryMetadata, StoryData, GameState
from nltk.tokenize import sent_tokenize
class StoryEngine:
    def __init__(self, story_file: str):
        self.story_data = self.load_story(story_file)
        self.game_state = GameState(location="start", inventory={}, flags=[])
        self.narrative_pipeline = pipeline('text-generation', model='microsoft/DialoGPT-medium') # or your model

    def load_story(self, story_file: str) -> StoryData:
        """Loads the story from a JSON file and returns a StoryData object."""
        try:
            with open(story_file, 'r') as f:
                story_data = json.load(f)
            # Parse the story data using the Pydantic models
            return StoryData(**story_data)
        except FileNotFoundError:
            raise FileNotFoundError(f"Story file '{story_file}' not found.")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in '{story_file}'.")
        except Exception as e:
            raise ValueError(f"Error loading story: {e}")

    def get_current_scene(self) -> Scene:
        """Returns the current scene based on the game state."""
        scene = next((s for s in self.story_data.scenes if s.id == self.game_state.location), None)
        if scene is None:
            raise ValueError(f"Scene with id '{self.game_state.location}' not found.")
        return scene

    def process_command(self, command: str) -> str:
        """Processes the given command and updates the game state."""
        print(f"Processing command: {command}")  # Log the command being processed
        command = command.lower()
        scene = self.get_current_scene()
        print(f"Current scene: {scene.id}")  # Log the current scene ID

        if command.startswith("go "):
            direction = command[3:].strip()
            for choice in scene.choices:
                if choice.action == f"go {direction}":
                    self.game_state.location = choice.next_scene
                    return f"You went {direction}."
            return "You can't go that way."
        elif command.startswith("take "):
            item_name = command[5:].strip()
            print(f"Attempting to take item: {item_name}")  # Log the item name

            # Find the item in the scene
            item = next((i for i in scene.items if i.name == item_name), None)

            if item:
                print(f"Item found: {item.name}")
                self.game_state.inventory[item.name] = item # Add the item to the inventory
                scene.items = [i for i in scene.items if i.name != item.name]  # Remove from scene
                print(f"Item '{item_name}' added to inventory and removed from scene.")  # Log the action
                return f"You took the {item_name}."
            else:
                print(f"Item not found in scene.")  # Log that the item was not found
                return f"You can't take the {item_name}."
        elif command.startswith("drop "):
            item_name = command[5:].strip()
            if item_name in self.game_state.inventory:
                del self.game_state.inventory[item_name]
                # Add the item back to the scene (simplified, no item properties)
                scene.items.append(Item(name=item_name, description="A dropped item", properties={}))
                return f"You dropped the {item_name}."
            return f"You don't have the {item_name}."
        elif command == "inventory":
            if not self.game_state.inventory:
                return "You aren't carrying anything."
            else:
                return f"You are carrying: {', '.join(self.game_state.inventory.keys())}"
        elif command.startswith("use "):
            item_name = command[4:].strip()
            if item_name in self.game_state.inventory:
                item_properties = self.game_state.inventory[item_name]
                if "damage" in item_properties:
                    damage = item_properties["damage"]
                    return f"You use the {item_name} and inflict {damage} damage!"
                elif "heal" in item_properties:
                    heal = item_properties["heal"]
                    return f"You use the {item_name} and heal {heal} health!"
                else:
                    return f"You use the {item_name}, but it doesn't seem to have any effect."
            else:
                return f"You don't have a {item_name} in your inventory."
        elif command.startswith("save "):
            save_file = command[5:].strip()
            self.save_game(save_file)
            return f"Game saved to {save_file}"
        elif command.startswith("load "):
            save_file = command[5:].strip()
            self.load_game(save_file)
            return f"Game loaded from {save_file}"
        else:
            # Check for other actions defined in choices
            for choice in scene.choices:
                if choice.action == command:
                    if self.evaluate_condition(choice.condition):
                        self.game_state.location = choice.next_scene

                        # Apply choice effects
                        if choice.add_inventory:
                            self.game_state.inventory.append(choice.add_inventory)
                        if choice.set_flag:
                            if choice.set_flag not in self.game_state.flags:
                                self.game_state.flags.append(choice.set_flag)
                                print(f"Flag '{choice.set_flag}' added to game state.")

                        return f"You {choice.action}."
                    else:
                        return "You can't do that yet."
            return "Invalid command."
    

    def clean_generated_text(self, text: str) -> str:
        sentences = sent_tokenize(text)
        cleaned = []
        seen = set()
        for s in sentences:
            s_lower = s.strip().lower()
            if s_lower and s_lower not in seen:
                cleaned.append(s.strip())
                seen.add(s_lower)
            if len(cleaned) == 2:
                break
        return " ".join(cleaned)

    def generate_dynamic_text(self, prompt: str, max_length: int = 30) -> str:
        scene = self.get_current_scene()
        base_description = next(
            (d['text'] for d in scene.descriptions if 'condition' not in d or self.evaluate_condition(d['condition'])),
            scene.descriptions[0]['text']
        )

        # DialoGPT works better with conversational-style prompts
        enhanced_prompt = f"{base_description} You also notice"

        try:
            # Minimal, safe parameters for DialoGPT
            generated = self.narrative_pipeline(
                enhanced_prompt,
                max_new_tokens=25,  
                do_sample=True,
                temperature=0.7,    
                top_p=0.8,          
                pad_token_id=self.narrative_pipeline.tokenizer.eos_token_id
            )

            full_text = generated[0]['generated_text']
    
            # Extract only the new content after the prompt
            continuation = full_text[len(enhanced_prompt):].strip()
    
            # Clean up the generated text
            if continuation:
                # Take only the first sentence
                sentences = sent_tokenize(continuation)
                if sentences:
                    sentence = sentences[0].strip()
            
                    # Clean up common generation artifacts
                    sentence = sentence.replace('\n', ' ').replace('\t', ' ')
                    sentence = ' '.join(sentence.split())  # Remove extra whitespace
                
                    # Remove DialoGPT-specific artifacts
                    dialogpt_artifacts = ['<|endoftext|>', '<|im_end|>', '</s>', '<s>']
                    for artifact in dialogpt_artifacts:
                        sentence = sentence.replace(artifact, '')
            
                    # Remove incomplete sentences or weird artifacts
                    if len(sentence) < 5 or len(sentence.split()) > 20:
                        return ""
            
                    # Ensure proper capitalization and punctuation
                    if sentence and not sentence[0].isupper():
                        sentence = sentence[0].upper() + sentence[1:]
            
                    if sentence and sentence[-1] not in '.!?':
                        sentence += '.'
            
                    # Basic quality check - avoid nonsensical outputs
                    if any(word in sentence.lower() for word in ['[', ']', '###', 'prompt:', 'scene:', 'notice']):
                        return ""
            
                    return sentence

        except Exception as e:
            print(f"Error generating dynamic text: {e}")
            return ""

        return ""

    def get_scene_output(self) -> Dict[str, Any]:
        """Returns the output for the current scene in a structured format."""
        scene = self.get_current_scene()
    
        # Find the appropriate description based on flags
        description = next(
            (d['text'] for d in scene.descriptions if 'condition' not in d or self.evaluate_condition(d['condition'])), 
            scene.descriptions[0]['text']
        )

        # Generate dynamic add-on description
        dynamic_addon = self.generate_dynamic_text("", max_length=25)
    
        # Only add dynamic content if it's meaningful
        full_description = description
        if dynamic_addon and len(dynamic_addon.strip()) > 0:
            full_description += " " + dynamic_addon

        return {
            "scene_id": scene.id,
            "description": full_description,
            "items": [item.name for item in scene.items],
            "choices": [choice.action for choice in scene.choices if self.evaluate_condition(choice.condition)],
            "inventory": list(self.game_state.inventory.keys()),
            "location": self.game_state.location,
            "flags": self.game_state.flags
        }

    def evaluate_condition(self, condition: Optional[str]) -> bool:
        """Evaluates a boolean expression involving flags."""
        if condition is None:
            return True

        # Replace flag names with their boolean values in game_state.flags
        # and use eval() to evaluate the expression
        try:
            # Create a local namespace for eval() with the flags
            flag_values = {flag: flag in self.game_state.flags for flag in self.game_state.flags}
            return eval(condition, {}, flag_values)
        except Exception as e:
            print(f"Error evaluating condition '{condition}': {e}")
            return False

    def save_game(self, save_file: str):
        """Saves the game state to a JSON file, ensuring the filename ends with .json."""
        if not save_file.endswith(".json"):
            save_file += ".json"
        try:
            with open(save_file, 'w') as f:
                json.dump(self.game_state.dict(), f, indent=2)
            print(f"Game saved to {save_file}")
        except Exception as e:
            print(f"Error saving game: {e}")

    def load_game(self, save_file: str):
        """Loads the game state from a JSON file."""
        try:
            with open(save_file, 'r') as f:
                game_state_data = json.load(f)
            self.game_state = GameState(**game_state_data)
            print(f"Game loaded from {save_file}")
        except FileNotFoundError:
            print(f"Save file '{save_file}' not found. Starting a new game.")
            self.game_state = GameState(location="start", inventory={}, flags=[])
        except json.JSONDecodeError:
            print(f"Invalid JSON format in '{save_file}'. Starting a new game.")
            self.game_state = GameState(location="start", inventory={}, flags=[])
        except Exception as e:
            print(f"Error loading game: {e}. Starting a new game.")
            self.game_state = GameState(location="start", inventory={}, flags=[])

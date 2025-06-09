import json
import os

def load_story(filename="story.json"):
    """Loads the story from a JSON file."""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {filename}.")
        return None

def save_story(data, filename="story.json"):
    """Saves the story to a JSON file."""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Story saved to {filename}")
    except Exception as e:
        print(f"Error saving story: {e}")

def add_scene(data):
    """Adds a new scene to the story."""
    print("\nAdding a new scene:")
    scene_id = input("Enter scene ID: ")
    # description = input("Enter scene description: ") #old

    descriptions = []
    while True:
        description_text = input("Enter scene description (or leave blank to finish): ")
        if not description_text:
            break
        description_condition = input(f"Enter condition for description '{description_text}' (or leave blank for always): ")
        description = {"text": description_text}
        if description_condition:
            description["condition"] = description_condition
        descriptions.append(description)

    items = []
    while True:
        item_name = input("Enter item name (or leave blank to finish): ")
        if not item_name:
            break
        item_description = input(f"Enter description for {item_name}: ")
        item_properties_str = input(f"Enter properties for {item_name} (JSON format, e.g., {{\"damage\": 10}} or leave blank): ")
        try:
            item_properties = json.loads(item_properties_str) if item_properties_str else {}
        except json.JSONDecodeError:
            print("Invalid JSON format for item properties.  Skipping properties.")
            item_properties = {}
        items.append({"name": item_name, "description": item_description, "properties": item_properties})

    choices = []
    while True:
        action = input("Enter choice action (or leave blank to finish): ")
        if not action:
            break
        next_scene = input(f"Enter next scene for action '{action}': ")
        add_inventory = input(f"Enter item to add to inventory for action '{action}' (or leave blank): ")
        set_flag = input(f"Enter flag to set for action '{action}' (or leave blank): ")
        condition = input(f"Enter condition for action '{action}' (or leave blank for always): ")

        choice = {"action": action, "next_scene": next_scene}
        if add_inventory:
            choice["add_inventory"] = add_inventory
        if set_flag:
            choice["set_flag"] = set_flag
        if condition:
            choice["condition"] = condition
        choices.append(choice)

    flags = []
    while True:
        flag = input("Enter scene flag (or leave blank to finish): ")
        if not flag:
            break
        flags.append(flag)

    new_scene = {
        "id": scene_id,
        "descriptions": descriptions,
        "items": items,
        "choices": choices,
        "flags": flags
    }

    data["scenes"].append(new_scene)
    print(f"Scene '{scene_id}' added.")

def edit_scene(data):
    """Edits an existing scene in the story."""
    print("\nEditing a scene:")
    scenes = data["scenes"]
    if not scenes:
        print("No scenes to edit.")
        return

    print("Available scenes:")
    for i, scene in enumerate(scenes):
        print(f"{i+1}. {scene['id']}: {scene['descriptions'][0]['text'][:50]}...")  # Truncate description

    while True:
        try:
            scene_index = int(input("Enter the number of the scene to edit (or leave blank to cancel): ")) - 1
            if scene_index < 0:
                return #cancel
            selected_scene = scenes[scene_index]
            break
        except ValueError:
            print("Invalid input. Please enter a number.")
        except IndexError:
            print("Invalid scene number.")
            return

    print(f"\nEditing scene: {selected_scene['id']}")

    while True:  # Editing loop
        print("\nScene attributes:")
        print("1. ID")
        print("2. Descriptions")
        print("3. Items")
        print("4. Choices")
        print("5. Flags")
        print("6. Back to main menu")

        attribute_choice = input("Enter the number of the attribute to edit: ")

        if attribute_choice == "1":
            new_id = input("Enter new scene ID: ")
            selected_scene["id"] = new_id
        elif attribute_choice == "2":
            print("Editing descriptions:")
            selected_scene["descriptions"] = []
            while True:
                description_text = input("Enter scene description (or leave blank to finish): ")
                if not description_text:
                    break
                description_condition = input(f"Enter condition for description '{description_text}' (or leave blank for always): ")
                description = {"text": description_text}
                if description_condition:
                    description["condition"] = description_condition
                selected_scene["descriptions"].append(description)

        elif attribute_choice == "3":
            print("Editing items is not yet implemented.  Sorry!")
        elif attribute_choice == "4":
             print("Editing choices is not yet implemented. Sorry!")
        elif attribute_choice == "5":
            print("Editing flags is not yet implemented. Sorry!")
        elif attribute_choice == "6":
            break # Back to main menu
        else:
            print("Invalid choice.")

        print(f"Scene '{selected_scene['id']}' updated.")

def main():
    """Main function to run the story editor."""
    story_data = load_story()

    if story_data is None:
        return

    if "metadata" not in story_data:
        print("Adding default metadata...")
        story_data["metadata"] = {
            "title": "Untitled Story",
            "author": "Unknown",
            "version": "0.1"
        }

    if "scenes" not in story_data:
        print("Adding default scenes array...")
        story_data["scenes"] = []

    while True:
        print("\nStory Editor Menu:")
        print("1. Add Scene")
        print("2. Edit Scene")
        print("3. Save Story")
        print("4. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            add_scene(story_data)
        elif choice == "2":
            edit_scene(story_data)
        elif choice == "3":
            save_story(story_data)
        elif choice == "4":
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()

from core.engine import StoryEngine
import argparse

def run_cli(save_file):
    """Runs the story engine in CLI mode."""
    engine = StoryEngine(story_file="story.json")
    engine.load_game(save_file) # load on startup
    while True:
        scene_output = engine.get_scene_output()
        print(scene_output['description'])
        print(f"Items: {', '.join(scene_output['items'])}")
        print(f"Inventory: {', '.join(scene_output['inventory'])}")
        print(f"Flags: {', '.join(scene_output['flags'])}")
        for choice in scene_output['choices']:
            print(f"- {choice}")
        command = input("> ")
        message = engine.process_command(command)
        print(message)
        print("-" * 20)  # Separator

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Story Engine.")
    parser.add_argument("--mode", choices=["api", "cli"], default="api", help="Run in 'api' (FastAPI) or 'cli' mode.")
    parser.add_argument("--save_file", default="save.json", help="Save file for game state.") #new
    args = parser.parse_args()

    if args.mode == "api":
        import uvicorn
        from api import app
        uvicorn.run(app, host="0.0.0.0", port=8000)
    elif args.mode == "cli":
        run_cli(args.save_file)

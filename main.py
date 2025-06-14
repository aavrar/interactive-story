import uvicorn
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Story Engine.")
    parser.add_argument("--mode", choices=["api", "cli"], default="api", help="Run in 'api' (FastAPI) or 'cli' mode.")
    parser.add_argument("--save_file", default="save.json", help="Save file for game state.")
    args = parser.parse_args()

    if args.mode == "api":
        uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
    elif args.mode == "cli":
        from cli import run_cli
        run_cli(args.save_file)
import argparse
import os
import subprocess
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.simulation.simulation_model import SimulationModel
from src.utils.config_loader import ConfigLoader


def main():
    """Parse command line arguments and run simulation."""
    parser = argparse.ArgumentParser(description='Run wildfire simulation')

    parser.add_argument('--config', '-c', type=str, default=None,
                        help='Path to configuration file')

    parser.add_argument('--visualise', '-v', action='store_true',
                        help='Run with visualisation')

    parser.add_argument('--output-gif', '-o', type=str, default=None,
                        help='Save visualization as GIF')

    parser.add_argument('--dev', '-d', action='store_true',
                        help='Run in development mode with auto-reload')

    args = parser.parse_args()

    if args.visualise:
        command = ["solara", "run"]
        command.append("src/visualisation/solara/solara_app.py")

        # Add additional arguments as environment variables
        env = os.environ.copy()
        if args.config:
            env["WILDFIRE_CONFIG"] = args.config
        if args.output_gif:
            env["WILDFIRE_OUTPUT_GIF"] = args.output_gif

        if args.dev:
            # Run with file watcher in development mode
            try:
                from src.watch import run_with_watcher
                run_with_watcher(command, env)
            except ImportError:
                print("Watchdog not installed. Run 'pip install watchdog' for development mode.")
                subprocess.run(command, env=env)
        else:
            # Run normally
            subprocess.run(command, env=env)
    else:
        config = ConfigLoader(args.config)
        model = SimulationModel(config)
        model.run()


if __name__ == "__main__":
    main()

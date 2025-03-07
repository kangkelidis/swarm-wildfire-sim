import subprocess
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class ChangeHandler(FileSystemEventHandler):
    def __init__(self, command, env):
        self.command = command
        self.env = env
        self.process = None
        self.restart_process()

    def restart_process(self):
        if self.process:
            print("Stopping Solara...")
            self.process.terminate()
            self.process.wait()

        print("Starting Solara...")
        self.process = subprocess.Popen(self.command, env=self.env)

    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            print(f"Detected change in {event.src_path}")
            self.restart_process()


def run_with_watcher(command, env):
    """Run a command with auto-reload on file changes.

    Args:
        command: List containing the command and its arguments
        env: Environment variables to pass to the command
    """

    watch_paths = [
        "src/simulation",
        "src/agents",
        "src/models",
        "src/visualisation",
        "src/utils"
    ]

    # Set up the file watcher
    event_handler = ChangeHandler(command, env)
    observer = Observer()

    # Watch directories
    for path in watch_paths:
        observer.schedule(event_handler, path, recursive=True)

    observer.start()

    try:
        print("Development server running with auto-reload. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process:
            event_handler.process.terminate()

    observer.join()

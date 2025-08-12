import subprocess
import time
import pyautogui
import os
import sys

# Ensure the catan package is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def verify_setup_ui():
    """
    Launches the Catan UI, waits for it to load, and takes a screenshot.
    """
    # The UI script needs to be run from the root of the repository
    # so that the catan module can be found.
    # We can't easily do that with subprocess.Popen, so we'll rely on the PYTHONPATH.
    ui_process = None
    try:
        # Launch the UI
        ui_process = subprocess.Popen(["python3", "catan/src/ui.py"])

        # Wait for the UI to load
        time.sleep(3)

        # Take a screenshot
        screenshot = pyautogui.screenshot()
        screenshot.save("jules-scratch/verification/setup_phase_ui.png")

    finally:
        # Ensure the UI process is terminated
        if ui_process:
            ui_process.terminate()

if __name__ == "__main__":
    verify_setup_ui()

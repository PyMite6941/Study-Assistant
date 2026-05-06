# Modules for properly importing stuff
import os
import sys
# Modules for styling
from rich.console import Console
import questionary

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_stuff import StudyAssistant

class CLI:
    def __init__():
        studyai = StudyAssistant()
        console = Console(style="white on blue")
        while True:
            console.print("What is the task you want to complete?",title="Study Assistant CLI")
            choice = questionary.select(
                "",
                choices=[
                    "Add some notes via file upload",
                    "Ask a question",
                    "Exit",
                ],
                pointer='>'
            )
            if choice == "Add some notes via file upload":

                studyai.add_note_to_brain()
            elif choice == "Exit":
                break
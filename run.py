# Module to run the necessary programs
import subprocess
# Modules for styling
from rich.console import Console
from rich.panel import Panel
import questionary

console = Console()
while True:
    console.print(Panel("What should be launched?",title="Study Assistant"))
    choice = questionary.select(
        "",
        choices=[
            "CLI Interface",
            "Web Interface",
            "Exit",
        ],
        pointer='>'
    ).ask()
    if choice == "CLI Interface":
        subprocess.run(['python','cli/cli.py'])
    elif choice == "Web Interface":
        subprocess.run(['streamlit','run','web_stuff/Home.py'])
    elif choice == "Exit":
        break
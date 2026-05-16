# Modules for properly importing stuff
import os
import sys
# Modules for styling
from rich.console import Console
from rich.panel import Panel
import questionary

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_stuff import StudyAssistant

class CLI:
    def __init__(self):
        self.studyai = StudyAssistant()
        console = Console(style="white on blue")
        while True:
            console.print(Panel("What is the task you want to complete?",title="Study Assistant CLI"))
            choice = questionary.select(
                "",
                choices=[
                    "Add some notes via file upload",
                    "Ask a question",
                    "Quiz me on a topic",
                    "Exit",
                ],
                pointer='>'
            ).ask()
            if choice == "Add some notes via file upload":
                file_names = questionary.text("What files should be uploaded? (Add a space between each file name)\n> ").ask().strip().split()
                self.studyai.add_data(file_names)
            elif choice == "Ask a question":
                question = questionary.text("What are you wondering?\n> ").ask()
                print(self.studyai.search_data(question))
            elif choice == "Quiz me on a topic":
                previous_questions = []
                topic = questionary.text("What topic should be quizzed?\n> ").ask()
                adaptive_comment = None
                while True:
                    results = self.studyai.quiz_stuff(topic,previous_questions=previous_questions,comments=adaptive_comment)
                    if isinstance(results,str):
                        console.print(f"[bold red]{results}[/]")
                        break
                    answer = questionary.text(f"Question:\n{results['question']}\nAnswer (A/B/C/D, or 'done' to stop)\n> ").ask().strip().upper()
                    if answer == "DONE":
                        break
                    previous_questions.append(results['question'])
                    if results['answer'] == answer:
                        console.print("[bold green]Correct![/]")
                        adaptive_comment = f"The user got the last question right. Make the next question slightly harder but still on {topic}."
                    else:
                        console.print(f"[bold red]Incorrect![/] The correct answer was {results['answer']}.")
                        adaptive_comment = f"The user got the last question wrong (chose {answer}, correct was {results['answer']}). Make a similar question on the same concept to reinforce it."
            elif choice == "Exit":
                break
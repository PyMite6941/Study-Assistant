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
                results = self.studyai.quiz_stuff(topic)
                answer = questionary.text(f"Question:\n{results['question']}\nWhat is the answer? (A, B, C, or D)\n> ").ask().strip().upper()
                if results['answer'] == answer:
                    console.print("[bold green]Correct![/]")
                    previous_questions.append(results['question'])
                    self.studyai.quiz_stuff(topic,previous_questions=previous_questions,comments=f"The user got {results['question']} right with answer {answer}. Make a new question that is slightly harder but still tests the same concept. The user should be able to get this new question right if they understand the concept well.")
                else:
                    console.print(f"[bold red]Incorrect![/]\nThe correct answer is {results['answer']}.\nReview the relevant content and try again.")
                    previous_questions.append(results['question'])
                    self.studyai.quiz_stuff(topic,previous_questions=previous_questions,comments=f"The user got {results['question']} wrong with answer {answer}. Make a new question that is similar but tests the same concept but is not identical to the previous question. The user should be able to get this new question right if they understand the concept better.")
            elif choice == "Exit":
                break
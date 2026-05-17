# Modules for properly importing stuff
import os
import sys
import datetime
# Modules for styling
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import questionary

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_stuff import StudyAssistant

LLM_CHOICES = {"Ask a question","Quiz me on a topic","Create a study plan","Generate a concept map"}

class CLI:
    def __init__(self):
        self.studyai = StudyAssistant()
        console = Console(style="white on blue")
        while True:
            console.print(Panel("What is the task you want to complete?",title="Study Assistant CLI"))
            choice = questionary.select(
                "",
                choices=[
                    "Add content (files or text)",
                    "Ask a question",
                    "Quiz me on a topic",
                    "Create a study plan",
                    "Generate a concept map",
                    "Settings",
                    "Exit",
                ],
                pointer='>'
            ).ask()
            if choice in LLM_CHOICES:
                ready, msg = self.studyai.check_chat_ready()
                if not ready:
                    console.print(f"[bold red]Unavailable:[/] {msg}")
                    continue
            if choice == "Add content (files or text)":
                method = questionary.select(
                    "How do you want to add content?",
                    choices=["From files","Type or paste text","Back"],
                    pointer='>'
                ).ask()
                if method == "From files":
                    raw = questionary.text("File path(s) — separate multiple with spaces\n> ").ask().strip()
                    if not raw:
                        console.print("[yellow]No files entered.[/]")
                    else:
                        file_names = raw.split()
                        results = self.studyai.add_data(file_names)
                        for name, ok, msg in results:
                            if ok:
                                console.print(f"[bold green]✓[/] {name}: {msg}")
                            else:
                                console.print(f"[bold red]✗[/] {name}: {msg}")
                elif method == "Type or paste text":
                    label = questionary.text("Label for this content (e.g. 'Chapter 3 notes')\n> ").ask().strip() or "manual input"
                    console.print("[dim]Type or paste your notes below. Enter a blank line then type END to finish.[/]")
                    lines = []
                    while True:
                        try:
                            line = input()
                        except EOFError:
                            break
                        if line.strip().upper() == "END" and lines and lines[-1].strip() == "":
                            break
                        lines.append(line)
                    text = "\n".join(lines).strip()
                    if text:
                        count = self.studyai.add_text(text, source_name=label)
                        console.print(f"[bold green]Added {count} chunk(s) under '{label}'.[/]")
                    else:
                        console.print("[yellow]No text entered.[/]")
            elif choice == "Ask a question":
                question = questionary.text("What are you wondering?\n> ").ask()
                gen, _ = self.studyai.search_data_stream(question)
                for chunk in gen:
                    print(chunk,end='',flush=True)
                print()
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
                        self.studyai.save_stats(topic,correct=True)
                        adaptive_comment = f"The user got the last question right. Make the next question slightly harder but still on {topic}."
                    else:
                        console.print(f"[bold red]Incorrect![/] The correct answer was {results['answer']}.")
                        self.studyai.save_stats(topic,correct=False)
                        adaptive_comment = f"The user got the last question wrong (chose {answer}, correct was {results['answer']}). Make a similar question on the same concept to reinforce it."
            elif choice == "Create a study plan":
                topic = questionary.text("What topic do you want to study?\n> ").ask()
                date_str = questionary.text("Target date (e.g. June 10, in 5 days) — leave blank for 7 days\n> ").ask().strip()
                if date_str:
                    topic, days = self.studyai._extract_study_plan_params(f"study plan for {topic} by {date_str}")
                else:
                    days = 7
                console.print(f"Generating a {days}-day study plan for '{topic}' ...")
                plan = self.studyai.create_study_plan(topic, days)
                if plan:
                    for day_info in plan['plan']:
                        console.print(Panel(
                            "\n".join(f"• {t}" for t in day_info.get('tasks',[])),
                            title=f"Day {day_info['day']}: {day_info.get('focus','')}"
                        ))
                    if questionary.confirm("Save this plan?").ask():
                        self.studyai.save_study_plan(plan)
                        console.print("[bold green]Plan saved![/]")
                else:
                    console.print("[bold red]Could not generate a plan. Add more notes on this topic first.[/]")
            elif choice == "Generate a concept map":
                topic = questionary.text("What topic?\n> ").ask()
                console.print(f"Extracting concepts for '{topic}' ...")
                triples = self.studyai.create_concept_map(topic)
                if triples:
                    table = Table(title=f"Concept Map: {topic}")
                    table.add_column("Concept A",style="cyan")
                    table.add_column("Relationship",style="yellow")
                    table.add_column("Concept B",style="cyan")
                    for t in triples:
                        if len(t) == 3:
                            table.add_row(t[0],t[1],t[2])
                    console.print(table)
                else:
                    console.print("[bold red]Could not extract concepts. Add more notes on this topic first.[/]")
            elif choice == "Settings":
                config = self.studyai.load_config()
                setting = questionary.select("What do you want to edit?", choices=[
                    "API Keys","Model Settings","Back"
                ]).ask()
                if setting == "API Keys":
                    for key in config["api_keys"]:
                        current = config["api_keys"][key]
                        display = f"{'*' * len(current) if current else '(empty)'}"
                        new_val = questionary.text(f"{key} [{display}] (leave blank to keep):\n> ").ask().strip()
                        if new_val:
                            config["api_keys"][key] = new_val
                    self.studyai.save_config(config)
                    console.print("[bold green]API keys saved.[/]")
                elif setting == "Model Settings":
                    for key in config["models"]:
                        current = config["models"][key]
                        new_val = questionary.text(f"{key} [{current}] (leave blank to keep):\n> ").ask().strip()
                        if new_val:
                            config["models"][key] = new_val
                    self.studyai.save_config(config)
                    self.studyai.asking_model = config["models"]["chat_model"]
                    console.print("[bold green]Model settings saved.[/]")
            elif choice == "Exit":
                break
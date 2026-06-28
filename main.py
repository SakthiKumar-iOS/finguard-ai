# main.py
# Purpose: Entry point for the finguard-ai Typer CLI exposing chat and audit commands.

import os
import glob
from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel

from config.settings import AUDIT_LOG_DIR
from agents.orchestrator import OrchestratorAgent

app = typer.Typer(help="FinGuard AI Command Line Interface")
console = Console()

@app.command()
def chat():
    """Start an interactive chat session with the Orchestrator Agent."""
    console.print(Panel("[bold green]Welcome to FinGuard AI![/bold green] Type 'exit' or 'quit' to end the session."))
    orchestrator = OrchestratorAgent()
    
    while True:
        try:
            user_input = console.input("[bold blue]You:[/bold blue] ")
            if user_input.strip().lower() in ("exit", "quit"):
                console.print("[bold yellow]Goodbye![/bold yellow]")
                break
            
            if not user_input.strip():
                continue
                
            response = orchestrator.run(user_input)
            console.print(f"[bold green]FinGuard:[/bold green] {response}")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold yellow]Goodbye![/bold yellow]")
            break

@app.command()
def audit():
    """Print the contents of the latest JSONL audit log file."""
    search_path = os.path.join(AUDIT_LOG_DIR, "*.jsonl")
    log_files = glob.glob(search_path)
    
    if not log_files:
        console.print(f"[bold red]No audit logs (*.jsonl) found in {AUDIT_LOG_DIR}[/bold red]")
        raise typer.Exit(code=1)
        
    # Sort files by modification time to get the latest
    latest_file = max(log_files, key=os.path.getmtime)
    console.print(Panel(f"[bold green]Displaying latest audit log file:[/bold green] {Path(latest_file).name}"))
    
    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            for line in f:
                console.print(line.strip())
    except Exception as e:
        console.print(f"[bold red]Error reading file {latest_file}: {e}[/bold red]")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()

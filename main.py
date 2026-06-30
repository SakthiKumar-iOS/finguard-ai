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
    # --- ADK Session Validator (runs once at startup) ---
    from agents.session_validator_adk import SessionValidatorAgent
    validator = SessionValidatorAgent()
    result = validator.validate()
    if not result["ready"]:
        issues_text = "\n".join(f"  • {issue}" for issue in result["issues"])
        console.print(Panel(
            f"[bold red]Session validation FAILED "
            f"({result['checks_passed']}/{result['checks_total']} checks passed)[/bold red]\n\n"
            f"{issues_text}\n\n"
            "[yellow]Fix the issues above and restart FinGuard AI.[/yellow]",
            title="[bold red]ADK Startup Check Failed[/bold red]",
            border_style="red",
        ))
        raise SystemExit(1)
    console.print(Panel(
        f"[bold green]Session validated via ADK — "
        f"{result['checks_passed']}/{result['checks_total']} checks passed. "
        f"Starting FinGuard AI...[/bold green]",
        title="[bold green]ADK Startup Check Passed[/bold green]",
        border_style="green",
    ))
    # --- End ADK Session Validator ---

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

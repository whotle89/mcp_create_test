"""
CLI Interface for Agent Orchestration System

Provides command-line interface for agent routing and execution.

Installation:
    pip install click rich

Usage:
    python cli_interface.py process "시간 거래 기능 만들어줘"
    python cli_interface.py verify ui-implementer app/time-slots
    python cli_interface.py metrics
"""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
import json

from main import AgentOrchestrator, AgentStatus


# Rich console for pretty output
console = Console()


@click.group()
@click.pass_context
def cli(ctx):
    """
    Agent Orchestration System CLI

    Manages routing and execution of UI and Logic implementation agents.
    """
    # Initialize orchestrator
    ctx.ensure_object(dict)
    ctx.obj['orchestrator'] = AgentOrchestrator(base_path=".")


@cli.command()
@click.argument('message')
@click.option('--path', '-p', help='Feature path (e.g., app/time-slots)')
@click.option('--json-output', '-j', is_flag=True, help='Output as JSON')
@click.pass_context
def process(ctx, message: str, path: str, json_output: bool):
    """
    Process user request and route to appropriate agent

    Examples:
        cli_interface.py process "시간 거래 기능 만들어줘"
        cli_interface.py process "Supabase 연결해줘" --path app/time-slots
    """
    orchestrator: AgentOrchestrator = ctx.obj['orchestrator']

    context = {}
    if path:
        context['current_path'] = path

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(description="Processing request...", total=None)

        result = orchestrator.process_request(message, context)

    if json_output:
        # JSON output
        console.print_json(json.dumps(result.to_dict(), indent=2))
    else:
        # Pretty output
        _display_execution_result(result)


@cli.command()
@click.argument('agent', type=click.Choice(['ui-implementer', 'feature-logic-implementer']))
@click.argument('feature_path')
@click.option('--json-output', '-j', is_flag=True, help='Output as JSON')
@click.pass_context
def verify(ctx, agent: str, feature_path: str, json_output: bool):
    """
    Verify that agent completed all required tasks

    Examples:
        cli_interface.py verify ui-implementer app/time-slots
        cli_interface.py verify feature-logic-implementer app/auth
    """
    orchestrator: AgentOrchestrator = ctx.obj['orchestrator']

    feature_path_obj = Path(feature_path)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(description="Verifying completion...", total=None)

        result = orchestrator.verify_agent_completion(agent, feature_path_obj)

    if json_output:
        console.print_json(json.dumps(result.to_dict(), indent=2))
    else:
        _display_execution_result(result)


@cli.command()
@click.argument('agent')
@click.argument('operation', type=click.Choice(['create', 'modify']))
@click.argument('file_path')
@click.pass_context
def check(ctx, agent: str, operation: str, file_path: str):
    """
    Check if file operation is allowed for agent

    Examples:
        cli_interface.py check feature-logic-implementer create app/time-slots/api.ts
        cli_interface.py check feature-logic-implementer modify app/time-slots/components/Form.tsx
    """
    orchestrator: AgentOrchestrator = ctx.obj['orchestrator']

    file_path_obj = Path(file_path)

    error = orchestrator.check_file_operation(agent, operation, file_path_obj)

    if error is None:
        console.print(Panel(
            f"[green]✅ Operation allowed[/green]\n\n"
            f"Agent: {agent}\n"
            f"Operation: {operation}\n"
            f"File: {file_path}",
            title="File Operation Check",
            border_style="green",
        ))
    else:
        console.print(Panel(
            f"[red]❌ Operation forbidden[/red]\n\n"
            f"{error}",
            title="File Operation Check",
            border_style="red",
        ))


@cli.command()
@click.option('--json-output', '-j', is_flag=True, help='Output as JSON')
@click.pass_context
def metrics(ctx, json_output: bool):
    """
    Display system metrics

    Examples:
        cli_interface.py metrics
        cli_interface.py metrics --json-output
    """
    orchestrator: AgentOrchestrator = ctx.obj['orchestrator']

    metrics_data = orchestrator.get_metrics()

    if json_output:
        console.print_json(json.dumps(metrics_data, indent=2))
    else:
        _display_metrics(metrics_data)


@cli.command()
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def history(ctx, output: str):
    """
    Export execution history

    Examples:
        cli_interface.py history
        cli_interface.py history --output history.json
    """
    orchestrator: AgentOrchestrator = ctx.obj['orchestrator']

    output_file = Path(output) if output else None

    history_json = orchestrator.export_history(output_file)

    if output:
        console.print(f"[green]✅ History exported to {output}[/green]")
    else:
        console.print_json(history_json)


@cli.command()
def examples():
    """
    Show example commands
    """
    examples_text = """
[bold cyan]Example Commands:[/bold cyan]

[yellow]1. Request UI creation:[/yellow]
   python cli_interface.py process "시간 거래 목록 페이지 만들어줘"

[yellow]2. Request backend implementation:[/yellow]
   python cli_interface.py process "Supabase 연결해줘" --path app/time-slots

[yellow]3. Request full feature:[/yellow]
   python cli_interface.py process "회원가입 기능 만들어줘"

[yellow]4. Verify UI completion:[/yellow]
   python cli_interface.py verify ui-implementer app/time-slots

[yellow]5. Verify backend completion:[/yellow]
   python cli_interface.py verify feature-logic-implementer app/auth

[yellow]6. Check file operation:[/yellow]
   python cli_interface.py check feature-logic-implementer create app/time-slots/api.ts

[yellow]7. View metrics:[/yellow]
   python cli_interface.py metrics

[yellow]8. Export history:[/yellow]
   python cli_interface.py history --output history.json
"""
    console.print(Panel(examples_text, title="Examples", border_style="cyan"))


@cli.command()
@click.pass_context
def interactive(ctx):
    """
    Start interactive mode
    """
    orchestrator: AgentOrchestrator = ctx.obj['orchestrator']

    console.print(Panel(
        "[bold cyan]Agent Orchestration System - Interactive Mode[/bold cyan]\n\n"
        "Type your requests or commands:\n"
        "  - 'metrics' - Show metrics\n"
        "  - 'history' - Show history\n"
        "  - 'help' - Show help\n"
        "  - 'exit' - Exit interactive mode\n\n"
        "Or just type your feature request!",
        border_style="cyan",
    ))

    while True:
        try:
            user_input = console.input("\n[bold cyan]>[/bold cyan] ")

            if not user_input.strip():
                continue

            if user_input.lower() == 'exit':
                console.print("[yellow]Exiting interactive mode...[/yellow]")
                break

            elif user_input.lower() == 'metrics':
                metrics_data = orchestrator.get_metrics()
                _display_metrics(metrics_data)

            elif user_input.lower() == 'history':
                history_json = orchestrator.export_history()
                console.print_json(history_json)

            elif user_input.lower() == 'help':
                console.print("""
[bold cyan]Available commands:[/bold cyan]
  metrics  - Show system metrics
  history  - Show execution history
  help     - Show this help
  exit     - Exit interactive mode

Or type a feature request like:
  "시간 거래 기능 만들어줘"
  "Supabase 연결해줘"
""")

            else:
                # Process as request
                result = orchestrator.process_request(user_input, {})
                _display_execution_result(result)

        except KeyboardInterrupt:
            console.print("\n[yellow]Exiting interactive mode...[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def _display_execution_result(result):
    """Display execution result in pretty format"""

    # Determine color based on status
    if result.status == AgentStatus.COMPLETED:
        color = "green"
        icon = "✅"
    elif result.status == AgentStatus.RUNNING:
        color = "blue"
        icon = "▶️"
    elif result.status == AgentStatus.BLOCKED:
        color = "yellow"
        icon = "⚠️"
    elif result.status == AgentStatus.FAILED:
        color = "red"
        icon = "❌"
    else:
        color = "white"
        icon = "ℹ️"

    # Create panel content
    content = f"{icon} [bold]{result.status.value.upper()}[/bold]\n\n"
    content += f"Agent: {result.agent}\n"
    content += f"Time: {result.timestamp}\n\n"
    content += result.message

    if result.files_created:
        content += "\n\n[bold]Files Created:[/bold]\n"
        content += "\n".join(f"  - {f}" for f in result.files_created)

    if result.files_modified:
        content += "\n\n[bold]Files Modified:[/bold]\n"
        content += "\n".join(f"  - {f}" for f in result.files_modified)

    if result.error:
        content += f"\n\n[red]Error: {result.error}[/red]"

    console.print(Panel(
        content,
        title=f"Execution Result - {result.agent}",
        border_style=color,
        box=box.ROUNDED,
    ))


def _display_metrics(metrics_data):
    """Display metrics in pretty format"""

    metrics = metrics_data['metrics']

    # Create metrics table
    table = Table(title="System Metrics", box=box.ROUNDED)

    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green", justify="right")

    table.add_row("Total Requests", str(metrics['total_requests']))
    table.add_row("Routed to UI", str(metrics['routed_to_ui']))
    table.add_row("Routed to Backend", str(metrics['routed_to_backend']))
    table.add_row("Successful Collaborations", str(metrics['successful_collaborations']))

    table.add_section()

    table.add_row("Blocked (Prerequisites)", str(metrics['blocked_missing_prerequisites']))
    table.add_row("Blocked (Incomplete UI)", str(metrics['blocked_incomplete_ui']))
    table.add_row("Blocked (File Conflicts)", str(metrics['blocked_file_conflicts']))

    table.add_section()

    success_rate = metrics_data['success_rate']
    success_color = "green" if success_rate > 0.9 else "yellow" if success_rate > 0.7 else "red"
    table.add_row("Success Rate", f"[{success_color}]{success_rate:.1%}[/{success_color}]")
    table.add_row("Total Executions", str(metrics_data['total_executions']))

    console.print(table)

    # Recent history
    if metrics_data['history']:
        console.print("\n[bold cyan]Recent History:[/bold cyan]")
        for entry in metrics_data['history'][-5:]:
            status_icon = "✅" if entry['status'] == "completed" else "⚠️" if entry['status'] == "blocked" else "❌"
            console.print(f"  {status_icon} {entry['agent']}: {entry['status']} - {entry['timestamp']}")


if __name__ == '__main__':
    cli(obj={})

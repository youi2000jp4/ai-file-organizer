"""CLI entry point for file-organizer."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from .config import CONFIG_FILE, load_config, save_config, set_api_key
from .models import ExecutionResult, OrganizePlan
from .organizer import Organizer

app = typer.Typer(
    name="file-org",
    help="[bold green]AI-powered file organizer[/bold green] — organize files with natural language.",
    rich_markup_mode="rich",
    no_args_is_help=True,
)
config_app = typer.Typer(help="Manage file-organizer configuration.")
app.add_typer(config_app, name="config")

console = Console()
err_console = Console(stderr=True)

# Known subcommand names — used by the main() entry point.
_SUBCOMMANDS: frozenset[str] = frozenset({"config", "organize"})


# ---------------------------------------------------------------------------
# Rich output helpers
# ---------------------------------------------------------------------------


def _print_plan(plan: OrganizePlan, directory: Path) -> None:
    if not plan.moves:
        rprint("[yellow]No files matched the instruction.[/yellow]")
        return

    table = Table(title="Organization Plan", show_lines=True, highlight=True)
    table.add_column("Source", style="cyan", no_wrap=True)
    table.add_column("→ Destination", style="green")
    table.add_column("Reason", style="dim")

    for op in plan.moves:
        dest = str(Path(op.destination_folder) / Path(op.source_name).name)
        table.add_row(op.source_name, dest, op.reason)

    console.print(table)

    for w in plan.warnings:
        rprint(f"[yellow]⚠  {w}[/yellow]")


def _print_result(result: ExecutionResult) -> None:
    verb = "[dim](dry-run)[/dim] Would move" if result.dry_run else "Moved"

    if result.moved:
        table = Table(title=f"Results — {verb} {result.total_moved} file(s)", show_lines=True)
        table.add_column("Source", style="cyan")
        table.add_column("Destination", style="green")
        for src, dst in result.moved:
            table.add_row(str(src.name), str(dst))
        console.print(table)

    for path, reason in result.skipped:
        rprint(f"[yellow]  Skipped:[/yellow] {path.name} — {reason}")

    for path, reason in result.errors:
        rprint(f"[red]  Error:[/red] {path.name} — {reason}")

    color = "green" if not result.errors else "red"
    icon = "✓" if not result.errors else "✗"
    rprint(
        f"\n[{color}]{icon}  {result.total_moved} moved"
        f", {result.total_skipped} skipped"
        f", {result.total_errors} errors[/{color}]"
    )


# ---------------------------------------------------------------------------
# organize command
# ---------------------------------------------------------------------------


@app.command()
def organize(
    instruction: str = typer.Argument(..., help="Natural language instruction (Japanese OK)"),
    target: Optional[Path] = typer.Argument(default=None, help="Target directory [default: current dir]"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Preview without moving files"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Scan subdirectories recursively"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Override LLM model"),
    max_files: Optional[int] = typer.Option(None, "--max-files", help="Max files to send to LLM"),
) -> None:
    """Organize files with a natural language instruction.

    Examples:

      file-org "Sort by file type"

      file-org "ダウンロードフォルダを種類別に整理して" ~/Downloads --dry-run

      file-org "Move screenshots to 2026 folder" --yes
    """
    directory = (target or Path.cwd()).resolve()
    if not directory.is_dir():
        err_console.print(f"[red]Error:[/red] '{directory}' is not a directory.")
        raise typer.Exit(1)

    cfg = load_config()
    if model:
        cfg.model = model
    if max_files:
        cfg.max_files = max_files

    if not cfg.has_api_key():
        err_console.print(
            "[red]Error:[/red] No API key configured.\n"
            "Run: [bold]file-org config set-key YOUR_KEY[/bold]\n"
            "Or set the [bold]OPENAI_API_KEY[/bold] environment variable."
        )
        raise typer.Exit(1)

    organizer = Organizer(cfg)

    with console.status(f"[bold cyan]Scanning '{directory}'…[/bold cyan]"):
        files = organizer.scan_files(directory, recursive)

    if not files:
        rprint("[yellow]No files found in the target directory.[/yellow]")
        raise typer.Exit(0)

    rprint(
        Panel(
            f"[bold]{len(files)}[/bold] files found in [cyan]{directory}[/cyan]\n"
            f"Instruction: [italic]{instruction}[/italic]"
            + ("  [dim](dry-run)[/dim]" if dry_run else ""),
            title="[bold green]file-org[/bold green]",
            border_style="green",
        )
    )

    with console.status("[bold cyan]Asking AI for organization plan…[/bold cyan]"):
        plan = asyncio.run(organizer.plan(instruction, directory, recursive))

    _print_plan(plan, directory)

    if not plan.moves:
        raise typer.Exit(0)

    if not dry_run and not yes and cfg.confirm_before_execute:
        confirmed = Confirm.ask(
            f"\nProceed with moving [bold]{len(plan.moves)}[/bold] file(s)?",
            default=False,
        )
        if not confirmed:
            rprint("[yellow]Aborted.[/yellow]")
            raise typer.Exit(0)

    with console.status("[bold cyan]Executing…[/bold cyan]", spinner="dots"):
        result = organizer.execute(plan, directory, dry_run=dry_run)

    _print_result(result)

    if result.total_errors:
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# config subcommands
# ---------------------------------------------------------------------------


@config_app.command("show")
def config_show() -> None:
    """Show current configuration."""
    cfg = load_config()
    table = Table(title="Current Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("provider", cfg.provider)
    table.add_row("model", cfg.effective_model)
    table.add_row("max_files", str(cfg.max_files))
    table.add_row("confirm_before_execute", str(cfg.confirm_before_execute))
    table.add_row("api_key", "***set***" if cfg.has_api_key() else "[red]not set[/red]")
    table.add_row("config_file", str(CONFIG_FILE))
    console.print(table)


@config_app.command("set-key")
def config_set_key(
    api_key: str = typer.Argument(..., help="API key"),
    provider: str = typer.Option("openai", "--provider", "-p", help="Provider: openai or xai"),
) -> None:
    """Save an API key (stored in ~/.config/file-organizer/.env, chmod 600)."""
    if provider not in ("openai", "xai"):
        err_console.print("[red]Provider must be 'openai' or 'xai'.[/red]")
        raise typer.Exit(1)
    set_api_key(api_key, provider=provider)  # type: ignore[arg-type]
    rprint(f"[green]✓[/green] API key saved for provider '{provider}'.")


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Config key"),
    value: str = typer.Argument(..., help="Config value"),
) -> None:
    """Set a configuration value (e.g. model, max_files, provider)."""
    cfg = load_config()
    allowed = {"model", "max_files", "provider", "confirm_before_execute", "create_backup"}
    if key not in allowed:
        err_console.print(f"[red]Unknown key '{key}'.[/red] Allowed: {', '.join(sorted(allowed))}")
        raise typer.Exit(1)

    data = cfg.model_dump(exclude={"openai_api_key", "xai_api_key"})
    if key in ("max_files",):
        data[key] = int(value)
    elif key in ("confirm_before_execute", "create_backup"):
        data[key] = value.lower() in ("true", "1", "yes")
    else:
        data[key] = value

    new_cfg = cfg.model_copy(update=data)
    save_config(new_cfg)
    rprint(f"[green]✓[/green] Set [cyan]{key}[/cyan] = [green]{value}[/green]")


@config_app.command("init")
def config_init() -> None:
    """Create a default config file at ~/.config/file-organizer/config.toml."""
    cfg = load_config()
    save_config(cfg)
    rprint(f"[green]✓[/green] Config initialized at [cyan]{CONFIG_FILE}[/cyan]")
    rprint("Next step: [bold]file-org config set-key YOUR_OPENAI_KEY[/bold]")


# ---------------------------------------------------------------------------
# Entry point — routes bare `file-org "text"` → `file-org organize "text"`
# ---------------------------------------------------------------------------


def main() -> None:
    """Installed entry point.

    Transparently injects 'organize' when the first argument is not a known
    subcommand, allowing `file-org "instruction"` without an explicit verb.
    """
    args = sys.argv[1:]
    if args and not args[0].startswith("-") and args[0] not in _SUBCOMMANDS:
        sys.argv.insert(1, "organize")
    app()

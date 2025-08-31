"""Development tasks for shake-n-bake."""

from pathlib import Path

from invoke import Context, task
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Project paths
ROOT = Path(__file__).parent
SRC = ROOT / "src"
TESTS = ROOT / "tests"

console = Console()


@task
def clean(ctx: Context) -> None:
    """Clean up build artifacts and cache files."""
    console.print("🧹 [bold blue]Cleaning up build artifacts...[/]")

    patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        "**/.pytest_cache",
        "**/.mypy_cache",
        "**/.coverage",
        "**/htmlcov",
        "**/*.egg-info",
        "**/dist",
        "**/build",
    ]

    cleaned_items = []
    for pattern in patterns:
        for path in ROOT.glob(pattern):
            if path.is_dir():
                ctx.run(f"rm -rf {path}", hide=True)
                cleaned_items.append(f"📁 {path}")
            else:
                ctx.run(f"rm -f {path}", hide=True)
                cleaned_items.append(f"📄 {path}")

    if cleaned_items:
        console.print(f"Cleaned {len(cleaned_items)} items")
    else:
        console.print("No artifacts to clean")

    console.print("✅ [bold green]Cleanup complete[/]")


@task
def format(ctx: Context) -> None:
    """Format code with ruff."""
    with console.status("[bold blue]Formatting code with ruff...[/]"):
        result = ctx.run(f"uv run ruff format {SRC} {TESTS} tasks.py", hide=True)

    if result.ok:
        console.print("✅ [bold green]Code formatted successfully[/]")
    else:
        console.print("❌ [bold red]Formatting failed[/]")
        console.print(result.stderr)


@task
def lint(ctx: Context) -> None:
    """Lint code with ruff."""
    with console.status("[bold blue]Linting code with ruff...[/]"):
        result = ctx.run(f"uv run ruff check {SRC} {TESTS} tasks.py", warn=True)

    if result.ok:
        console.print("✅ [bold green]No linting issues found[/]")
    else:
        console.print("❌ [bold red]Linting issues found[/]")
        console.print(result.stdout)


@task
def lint_fix(ctx: Context) -> None:
    """Lint and auto-fix code with ruff."""
    with console.status("[bold blue]Linting and fixing code with ruff...[/]"):
        result = ctx.run(f"uv run ruff check --fix {SRC} {TESTS} tasks.py", hide=True)

    if result.ok:
        console.print("✅ [bold green]Lint fixes applied successfully[/]")
    else:
        console.print("❌ [bold red]Some linting issues could not be auto-fixed[/]")
        console.print(result.stdout)


@task
def typecheck(ctx: Context) -> None:
    """Type check code with mypy."""
    with console.status("[bold blue]Type checking with mypy...[/]"):
        result = ctx.run(f"uv run mypy {SRC}", warn=True)

    if result.ok:
        console.print("✅ [bold green]Type checking passed[/]")
    else:
        console.print("❌ [bold red]Type checking failed[/]")
        console.print(result.stdout)


@task
def test(ctx: Context, verbose: bool = False, coverage: bool = True, watch: bool = False) -> None:
    """Run tests with pytest."""
    console.print("🧪 [bold blue]Running tests...[/]")

    cmd_parts = ["uv run pytest -n auto"]

    if verbose:
        cmd_parts.append("-v")

    if coverage:
        cmd_parts.extend(
            [
                "--cov=shake_n_bake",
                "--cov-report=term-missing",
                "--cov-report=html",
            ]
        )

    if watch:
        cmd_parts.append("-f")

    cmd_parts.append(str(TESTS))

    result = ctx.run(" ".join(cmd_parts), warn=True)

    if result.ok:
        console.print("✅ [bold green]All tests passed![/]")
        if coverage:
            console.print("📊 [dim]Coverage report generated in htmlcov/[/]")
    else:
        console.print("❌ [bold red]Some tests failed[/]")


@task
def quality(ctx: Context) -> None:
    """Run all quality checks (format, lint, typecheck, test)."""
    console.print(Panel.fit("🚀 [bold]Running Quality Checks[/]", border_style="blue"))

    checks = [
        ("Format", format),
        ("Lint", lint),
        ("Type Check", typecheck),
        ("Test", test),
    ]

    results = {}
    for check_name, check_func in checks:
        console.print(f"\n[bold blue]Running {check_name}...[/]")
        try:
            check_func(ctx)
            results[check_name] = "✅ Pass"
        except Exception as e:
            results[check_name] = f"❌ Fail: {str(e)}"

    # Show summary table
    table = Table(title="Quality Check Results")
    table.add_column("Check", style="bold")
    table.add_column("Result")

    for check_name, result in results.items():
        style = "green" if "Pass" in result else "red"
        table.add_row(check_name, result, style=style)

    console.print(table)

    if all("Pass" in result for result in results.values()):
        console.print("\n🎉 [bold green]All quality checks passed![/]")
    else:
        console.print("\n💥 [bold red]Some quality checks failed[/]")


@task
def install(ctx: Context) -> None:
    """Install dependencies."""
    with console.status("[bold blue]Installing dependencies...[/]"):
        ctx.run("uv sync", hide=True)
    console.print("✅ [bold green]Dependencies installed[/]")


@task
def dev_install(ctx: Context) -> None:
    """Install development dependencies."""
    with console.status("[bold blue]Installing development dependencies...[/]"):
        ctx.run("uv sync --group dev", hide=True)
    console.print("✅ [bold green]Development dependencies installed[/]")


@task
def build(ctx: Context) -> None:
    """Build the package."""
    with console.status("[bold blue]Building package...[/]"):
        result = ctx.run("uv build", hide=True)

    if result.ok:
        console.print("✅ [bold green]Package built successfully[/]")
    else:
        console.print("❌ [bold red]Build failed[/]")
        console.print(result.stderr)


@task
def run_shake_n_bake(ctx: Context, directory: str, target: str = "", *args) -> None:
    """Run shake-n-bake command."""
    cmd_parts = [f"uv run python -m shake_n_bake.cli {directory}"]

    if target:
        cmd_parts.append(target)

    if args:
        cmd_parts.extend(args)

    console.print(f"🔨 [bold blue]Running:[/] {' '.join(cmd_parts)}")
    ctx.run(" ".join(cmd_parts))


@task
def run_merge_convert(ctx: Context, *files) -> None:
    """Run merge-n-convert command."""
    if not files:
        console.print("❌ [bold red]Please specify JSON files to merge[/]")
        return

    cmd = f"uv run python -c 'from shake_n_bake.cli import merge_convert_app; merge_convert_app()' {' '.join(files)}"
    console.print(f"🔄 [bold blue]Merging files:[/] {', '.join(files)}")
    ctx.run(cmd)


@task
def setup(ctx: Context) -> None:
    """Set up development environment."""
    console.print(Panel.fit("🚀 [bold]Setting up Development Environment[/]", border_style="green"))

    dev_install(ctx)

    console.print("\n✅ [bold green]Development environment ready![/]")

    # Show available commands table
    table = Table(title="Available Commands", show_header=True, header_style="bold blue")
    table.add_column("Command", style="cyan")
    table.add_column("Description")

    commands = [
        ("inv test", "Run tests with coverage"),
        ("inv test --no-coverage", "Run tests without coverage"),
        ("inv lint", "Lint code with ruff"),
        ("inv lint-fix", "Lint and auto-fix issues"),
        ("inv format", "Format code with ruff"),
        ("inv typecheck", "Type check with mypy"),
        ("inv quality", "Run all quality checks"),
        ("inv clean", "Clean build artifacts"),
        ("inv build", "Build the package"),
    ]

    for command, description in commands:
        table.add_row(command, description)

    console.print(table)


@task
def docs_serve(ctx: Context, port: int = 8000) -> None:
    """Serve documentation locally (placeholder for future docs)."""
    console.print(f"📚 [bold blue]Would serve documentation on port {port}...[/]")
    console.print("📝 [yellow]Documentation not implemented yet[/]")


# Default task
@task(default=True)
def help(ctx: Context) -> None:
    """Show available tasks."""
    console.print(Panel.fit("📋 [bold]Available Tasks[/]", border_style="blue"))
    ctx.run("inv --list")

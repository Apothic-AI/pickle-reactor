#!/usr/bin/env python3
"""
Pickle-Reactor CLI

ANCHOR: cli.main
TITLE: Pickle-Reactor framework CLI entry point
ROLE: developer experience layer
EXPORTS: main, dev, build, test, info commands
SEE: server.app, tests/conftest.py

Commands:
  dev     - Start development server
  build   - Build for production (copies files to dist/)
  test    - Run test suite
  info    - Show framework info
"""

import click
import subprocess
import shutil
from pathlib import Path


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Pickle-Reactor Framework CLI"""
    pass


@main.command()
@click.option('--host', default='0.0.0.0', help='Host to bind (default: 0.0.0.0)')
@click.option('--port', default=8000, type=int, help='Port to bind (default: 8000)')
@click.option('--reload/--no-reload', default=True, help='Enable hot reload (default: enabled)')
def dev(host, port, reload):
    """
    Start development server with hot reload.

    ANCHOR: cli.dev
    TITLE: Development server command
    SEE: server.app.app

    This starts a uvicorn server with hot reload enabled for rapid development.
    The server watches Python files and automatically restarts on changes.

    Browser auto-refresh requires manual reload (F5) after server restart.
    """
    click.echo("╔════════════════════════════════════════════╗")
    click.echo("║    Pickle-Reactor Development Server       ║")
    click.echo("╚════════════════════════════════════════════╝")
    click.echo()
    click.echo(f"🚀 Starting server on http://{host}:{port}")

    if reload:
        click.echo("📦 Hot reload enabled (watches Python files)")
        click.echo("   ℹ️  Server restarts automatically on file changes")
        click.echo("   ℹ️  Refresh browser (F5) after restart")
    else:
        click.echo("📦 Hot reload disabled")

    click.echo()
    click.echo("Press Ctrl+C to stop")
    click.echo()

    # Build uvicorn command
    cmd = [
        'uvicorn',
        'server.app:app',
        '--host', host,
        '--port', str(port),
    ]

    if reload:
        cmd.append('--reload')

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        click.echo()
        click.echo("✅ Server stopped")


@main.command()
@click.option('--output', default='dist', help='Output directory (default: dist)')
@click.option('--clean/--no-clean', default=True, help='Clean output directory first')
def build(output, clean):
    """
    Build for production.

    ANCHOR: cli.build
    TITLE: Production build command
    SEE: server.app, client.runtime, static/

    Copies all framework files to the output directory for deployment.
    The build includes:
    - Server code (FastAPI application)
    - Shared code (VDOM, state management)
    - Client code (Pyodide runtime)
    - Pages (user components)
    - Static assets (JavaScript, copied Python modules)
    """
    click.echo("╔════════════════════════════════════════════╗")
    click.echo("║    Pickle-Reactor Production Build         ║")
    click.echo("╚════════════════════════════════════════════╝")
    click.echo()

    output_dir = Path(output)

    # Clean output directory
    if clean and output_dir.exists():
        click.echo(f"🧹 Cleaning output directory: {output_dir}")
        shutil.rmtree(output_dir)

    output_dir.mkdir(exist_ok=True)

    # Copy directories
    dirs_to_copy = ['server', 'shared', 'pages', 'client', 'static']

    for dir_name in dirs_to_copy:
        src = Path(dir_name)
        if src.exists():
            click.echo(f"📦 Copying {dir_name}/")
            shutil.copytree(src, output_dir / dir_name, dirs_exist_ok=True)

    click.echo()
    click.echo(f"✅ Build complete! Output: {output_dir.absolute()}")
    click.echo()
    click.echo("📝 To deploy:")
    click.echo(f"   cd {output}")
    click.echo(f"   uvicorn server.app:app --host 0.0.0.0 --port 8000")
    click.echo()
    click.echo("📝 Or use a production ASGI server:")
    click.echo(f"   cd {output}")
    click.echo(f"   gunicorn server.app:app -w 4 -k uvicorn.workers.UvicornWorker")


@main.command()
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--markers', '-m', help='Run tests with specific markers (e.g., "unit" or "not e2e")')
@click.option('--coverage/--no-coverage', default=False, help='Generate coverage report')
def test(verbose, markers, coverage):
    """
    Run test suite.

    ANCHOR: cli.test
    TITLE: Test execution command
    SEE: tests/, pytest.ini

    Runs pytest with configured options. Use markers to run specific test types:
    - unit: Pure Python unit tests (fast)
    - integration: Integration tests with external services (moderate)
    - e2e: End-to-end browser tests (slow)

    Examples:
      pickle-reactor test              # Run all tests
      pickle-reactor test -m unit      # Run only unit tests
      pickle-reactor test -m "not e2e" # Run all except E2E tests
      pickle-reactor test --coverage   # Run with coverage report
    """
    click.echo("╔════════════════════════════════════════════╗")
    click.echo("║    Pickle-Reactor Test Suite               ║")
    click.echo("╚════════════════════════════════════════════╝")
    click.echo()

    cmd = ['pytest', 'tests/']

    if verbose:
        cmd.append('-v')

    if markers:
        cmd.extend(['-m', markers])
        click.echo(f"🧪 Running tests with markers: {markers}")
    else:
        click.echo("🧪 Running all tests")

    if coverage:
        cmd.extend(['--cov=shared', '--cov=server', '--cov=client', '--cov-report=term-missing'])
        click.echo("📊 Coverage report enabled")

    click.echo()

    result = subprocess.run(cmd)

    click.echo()
    if result.returncode == 0:
        click.echo("✅ All tests passed!")
    else:
        click.echo("❌ Tests failed!")
        raise SystemExit(result.returncode)


@main.command()
def info():
    """
    Show framework information.

    ANCHOR: cli.info
    TITLE: Framework information display

    Displays version, features, technology stack, and usage instructions.
    """
    click.echo("""
╔═══════════════════════════════════════════════════╗
║          Pickle-Reactor Framework                 ║
╚═══════════════════════════════════════════════════╝

Version: 0.1.0 (Phase 6 Complete - Production Ready)
Description: Next.js-style Python framework using Pyodide

╔═══════════════════════════════════════════════════╗
║  Features                                         ║
╚═══════════════════════════════════════════════════╝

  ✅ Server-Side Rendering (SSR)
  ✅ Virtual DOM with Preact-style diffing
  ✅ React-style hooks (use_state)
  ✅ File-based routing (/pages directory)
  ✅ Server actions & data loading
  ✅ Interactive components in browser (via Pyodide)
  ✅ Hot reload development server
  ✅ Production build system

╔═══════════════════════════════════════════════════╗
║  Technology Stack                                 ║
╚═══════════════════════════════════════════════════╝

  Backend:
    • FastAPI (ASGI web framework)
    • Uvicorn (ASGI server)
    • Python 3.11+ (server-side Python)

  Frontend:
    • Pyodide (Python in browser via WebAssembly)
    • PyScript pydom (DOM abstraction)
    • Vanilla JavaScript (bootstrap)

  Testing:
    • pytest (test framework)
    • httpx (HTTP client testing)
    • Playwright (E2E browser testing)

╔═══════════════════════════════════════════════════╗
║  Project Structure                                ║
╚═══════════════════════════════════════════════════╝

  server/      FastAPI application & SSR
  client/      Client-side runtime (Pyodide)
  shared/      Shared code (VDOM, state)
  pages/       Page components (file-based routing)
  static/      Static assets (JS, copied Python modules)
  tests/       Test suite (unit, integration, e2e)

╔═══════════════════════════════════════════════════╗
║  Commands                                         ║
╚═══════════════════════════════════════════════════╝

  pickle-reactor dev       Start development server
  pickle-reactor build     Build for production
  pickle-reactor test      Run test suite
  pickle-reactor info      Show this information

╔═══════════════════════════════════════════════════╗
║  Quick Start                                      ║
╚═══════════════════════════════════════════════════╝

  1. Create a new page:

     # pages/hello.py
     from shared.vdom import div, h1, button
     from shared.state import use_state

     def HelloPage(props):
         count, set_count = use_state(0)

         return div(
             {},
             h1({}, f"Hello! Count: {count}"),
             button(
                 {"on_click": lambda e: set_count(count + 1)},
                 "Increment"
             )
         )

  2. Run the development server:

     pickle-reactor dev

  3. Open in browser:

     http://localhost:8000

╔═══════════════════════════════════════════════════╗
║  Learn More                                       ║
╚═══════════════════════════════════════════════════╝

  Documentation: See README.md and docs/ folder
  Source Code:   https://github.com/yourusername/pickle-reactor
  Issues:        https://github.com/yourusername/pickle-reactor/issues

""")


if __name__ == '__main__':
    main()

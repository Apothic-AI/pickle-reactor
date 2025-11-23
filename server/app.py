# ANCHOR: server.app
# TITLE: FastAPI application with SSR and routing
# ROLE: server/http layer
# EXPORTS: app (FastAPI instance), ROUTES (routing registry)
# SEE: server.ssr.render-to-string, pages.index.IndexPage, tests.integration.test-server

"""
FastAPI application for pickle-reactor framework.

This module provides:
- HTTP server with SSR-rendered pages
- File-based routing with path→component registry
- Static file serving for Pyodide and client assets
- HTML shell template with Pyodide bootstrap

Phase 4: Routing & Multiple Pages
- ROUTES registry maps URL paths to (component, component_name) tuples
- Route handler selects component based on path
- Component name embedded in HTML for client hydration

SECURITY:
- CSP headers configured for WASM execution
- HTML escaping via render_to_string
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from server.ssr import render_to_string
from server.actions import router as actions_router, _todos_db  # Phase 5: Server actions
from pages.index import IndexPage
from pages.about import AboutPage
from pages.todos import TodosPage
from pages.dashboard import DashboardPage  # Phase 5: Dashboard with data loading
from shared.state import ComponentInstance, render_component
import json  # Phase 5: For embedding initial props


# ANCHOR: server.app.instance
# Create FastAPI application
app = FastAPI(
    title="Pickle-Reactor",
    description="Next.js-style Python framework using Pyodide and VDOM",
    version="0.1.0"
)

# Mount static files directory for client assets
app.mount("/static", StaticFiles(directory="static"), name="static")

# Phase 5: Register server actions router
app.include_router(actions_router)


# ANCHOR: server.app.routes
# TITLE: File-based routing registry
# ROLE: routing layer
# SEE: server.app.route_handler, client.router, tests.unit.test-routing

# Phase 4: Routing Registry
# Maps URL paths to (component, component_name) tuples
# Convention: /pages/*.py files map to routes
#   pages/index.py → "/"
#   pages/about.py → "/about"
#   pages/todos.py → "/todos"
#   pages/dashboard.py → "/dashboard"  # Phase 5: With initial props
ROUTES = {
    "/": (IndexPage, "IndexPage"),
    "/about": (AboutPage, "AboutPage"),
    "/todos": (TodosPage, "TodosPage"),
    "/dashboard": (DashboardPage, "DashboardPage"),  # Phase 5
}


# ANCHOR: server.app.health
# TITLE: Health check endpoint
# ROLE: server/http layer
# SEE: tests.integration.test-server-routing

@app.get("/health")
async def health():
    """Health check endpoint.

    Returns:
        JSON with status OK and current phase

    SEE: tests.integration.test-server-routing.TestHealthEndpoint
    """
    return {"status": "ok", "framework": "pickle-reactor", "phase": "4"}


# ANCHOR: server.app.route_handler
# TITLE: Dynamic route handler with component selection
# ROLE: routing/http layer
# SEE: server.app.routes, server.ssr.render-to-string, tests.integration.test-routing

@app.get("/{path:path}", response_class=HTMLResponse)
async def route_handler(path: str = ""):
    """Render page with SSR based on URL path.

    Phase 4: Dynamic routing
    - Looks up component in ROUTES registry based on path
    - Returns 404 for unknown routes
    - Embeds component name in HTML for client hydration
    - Supports multiple pages with file-based routing

    WHY: Server-side rendering provides initial HTML for fast page load,
    SEO benefits, and proper routing. Pyodide will hydrate the page
    client-side with the correct component.

    Args:
        path: URL path (e.g., "", "about", "todos")

    Returns:
        HTML string with SSR content and Pyodide bootstrap, or 404 JSON

    SEE: server.app.routes, pages.*.*, server.ssr.render-to-string, client.router
    """
    # Normalize path to match route keys
    route_path = "/" + path if path else "/"

    # Lookup component in routing registry
    if route_path not in ROUTES:
        return JSONResponse(
            {
                "error": "Page not found",
                "path": route_path,
                "available_routes": list(ROUTES.keys())
            },
            status_code=404
        )

    # Get component and component name from registry
    component, component_name = ROUTES[route_path]

    # Phase 5: Load initial data for pages that need it
    initial_props = {}
    if route_path == '/dashboard':
        # Fetch todos and compute stats for dashboard
        todos = _todos_db  # From server.actions
        initial_props = {
            'data': {
                'total': len(todos),
                'done': sum(1 for t in todos if t['done']),
                'active': sum(1 for t in todos if not t['done']),
            }
        }

    # Create component instance for SSR
    # On server, state is initialized but never updated (single-shot render)
    inst = ComponentInstance()

    # Render page component to HTML with state support
    # Phase 5: Pass initial props to component
    vnode = render_component(component, initial_props, inst)
    content_html = render_to_string(vnode)

    # Determine page title based on route
    page_titles = {
        "/": "Pickle-Reactor Framework",
        "/about": "About - Pickle-Reactor",
        "/todos": "Todos - Pickle-Reactor",
        "/dashboard": "Dashboard - Pickle-Reactor",  # Phase 5
    }
    page_title = page_titles.get(route_path, "Pickle-Reactor")

    # Phase 5: Serialize initial props to JSON for client hydration
    initial_props_json = json.dumps(initial_props) if initial_props else "{}"

    # Build complete HTML shell with Pyodide bootstrap
    # Phase 4: Embed component name for client-side hydration
    # Phase 5: Embed initial props for SSR data loading
    # SECURITY: CSP header allows 'wasm-unsafe-eval' required for Pyodide
    shell = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title}</title>
    <!-- Pyodide WebAssembly Python runtime -->
    <script src="https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js"></script>
    <!-- Phase 4: Embed page component name for client hydration -->
    <script>window.__PAGE_COMPONENT__ = '{component_name}';</script>
    <!-- Phase 5: Embed initial props for SSR data loading -->
    <script>window.__INITIAL_PROPS__ = {initial_props_json};</script>

    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            background: #f9f9f9;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .title {{
            color: #2563eb;
            margin-top: 0;
        }}
        .subtitle {{
            color: #64748b;
            font-size: 1.1rem;
        }}
        .highlight {{
            color: #2563eb;
            font-weight: 600;
        }}

        /* Phase 2: Counter Demo Styles */
        .counter-demo {{
            margin: 2rem 0;
            padding: 1.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 8px;
            color: white;
        }}
        .counter-demo h2 {{
            margin-top: 0;
            color: white;
        }}
        .counter {{
            background: rgba(255, 255, 255, 0.95);
            padding: 1.5rem;
            border-radius: 6px;
            color: #333;
            text-align: center;
        }}
        .count-display {{
            font-size: 2rem;
            font-weight: bold;
            color: #2563eb;
            margin: 1rem 0;
        }}
        .increment-btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 1rem 2rem;
            font-size: 1.1rem;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .increment-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }}
        .increment-btn:active {{
            transform: translateY(0);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .counter-info {{
            margin-top: 1rem;
            font-size: 0.9rem;
            color: #64748b;
        }}

        /* Phase 2: Counter Section */
        .counter-section {{
            margin: 2rem 0;
            padding: 1.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 8px;
            color: white;
        }}
        .counter-section h2 {{
            margin-top: 0;
            color: white;
        }}

        /* Phase 3: Todo List Styles */
        .todo-section {{
            margin: 2rem 0;
            padding: 1.5rem;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            border-radius: 8px;
            color: white;
        }}
        .todo-section h2 {{
            margin-top: 0;
            color: white;
        }}
        .add-todo-btn {{
            background: rgba(255, 255, 255, 0.95);
            color: #f5576c;
            border: none;
            padding: 0.75rem 1.5rem;
            font-size: 1rem;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }}
        .add-todo-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        .add-todo-btn:active {{
            transform: translateY(0);
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }}
        .todo-list {{
            list-style: none;
            padding: 0;
            margin: 1rem 0;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 6px;
            overflow: hidden;
        }}
        .todo-item {{
            display: flex;
            align-items: center;
            padding: 1rem;
            border-bottom: 1px solid #f1f5f9;
            transition: background-color 0.2s;
        }}
        .todo-item:last-child {{
            border-bottom: none;
        }}
        .todo-item:hover {{
            background-color: #f8fafc;
        }}
        .todo-item.done .todo-text {{
            text-decoration: line-through;
            opacity: 0.6;
        }}
        .todo-text {{
            flex: 1;
            color: #334155;
            font-size: 1rem;
        }}
        .todo-toggle {{
            background: #10b981;
            color: white;
            border: none;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            cursor: pointer;
            margin-right: 0.5rem;
            font-size: 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }}
        .todo-toggle:hover {{
            background: #059669;
            transform: scale(1.1);
        }}
        .todo-item.done .todo-toggle {{
            background: #64748b;
        }}
        .todo-remove {{
            background: #ef4444;
            color: white;
            border: none;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.2rem;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }}
        .todo-remove:hover {{
            background: #dc2626;
            transform: scale(1.1);
        }}
        .todo-info {{
            margin-top: 1rem;
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.9);
        }}

        .features {{
            margin: 2rem 0;
            padding: 1rem;
            background: white;
            border-radius: 4px;
        }}
        .features p {{
            margin: 0.5rem 0;
        }}
        .status {{
            margin-top: 2rem;
            padding: 1rem;
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            border-radius: 4px;
        }}
        .status.loaded {{
            background: #d1fae5;
            border-left-color: #10b981;
        }}
        .status p {{
            margin: 0;
        }}

        /* Phase 4: Navigation Styles */
        .nav {{
            margin-bottom: 2rem;
            padding: 1rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 8px;
            text-align: center;
        }}
        .nav-link {{
            color: white;
            text-decoration: none;
            font-weight: 600;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            transition: all 0.2s;
            display: inline-block;
        }}
        .nav-link:hover {{
            background: rgba(255, 255, 255, 0.2);
        }}
        .nav-link.active {{
            background: rgba(255, 255, 255, 0.3);
        }}

        /* Phase 4: About Page Styles */
        .section {{
            margin: 2rem 0;
            padding: 1.5rem;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .section h2 {{
            color: #2563eb;
            margin-top: 0;
        }}
        .features-list, .architecture-list, .tech-list, .phases-list {{
            list-style: none;
            padding: 0;
        }}
        .features-list li, .architecture-list li, .tech-list li, .phases-list li {{
            padding: 0.5rem 0;
            border-bottom: 1px solid #f1f5f9;
        }}
        .features-list li:last-child, .architecture-list li:last-child,
        .tech-list li:last-child, .phases-list li:last-child {{
            border-bottom: none;
        }}
        .tech-name {{
            font-weight: 600;
            color: #2563eb;
        }}
        .phase-complete {{
            color: #10b981;
        }}
        .phase-current {{
            color: #f59e0b;
            font-weight: 600;
        }}
        .phase-pending {{
            color: #64748b;
        }}
        .cta {{
            margin: 2rem 0;
            padding: 1.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 8px;
            text-align: center;
            color: white;
        }}
        .cta-link {{
            color: #fef3c7;
            font-weight: 600;
            text-decoration: none;
            border-bottom: 2px solid #fef3c7;
        }}
        .cta-link:hover {{
            border-bottom-color: white;
        }}

        /* Phase 4: Todos Page Styles */
        .todo-stats {{
            display: flex;
            justify-content: space-around;
            margin: 2rem 0;
            padding: 1.5rem;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .stat {{
            text-align: center;
        }}
        .stat-number {{
            display: block;
            font-size: 2rem;
            font-weight: bold;
            color: #2563eb;
        }}
        .stat-label {{
            color: #64748b;
            font-size: 0.9rem;
        }}
        .todo-input-section {{
            margin: 2rem 0;
            display: flex;
            gap: 1rem;
        }}
        .todo-input {{
            flex: 1;
            padding: 0.75rem 1rem;
            border: 2px solid #e2e8f0;
            border-radius: 6px;
            font-size: 1rem;
            transition: border-color 0.2s;
        }}
        .todo-input:focus {{
            outline: none;
            border-color: #2563eb;
        }}
        .todo-actions {{
            margin: 1rem 0;
            display: flex;
            gap: 1rem;
            justify-content: center;
        }}
        .action-btn {{
            background: #2563eb;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            font-size: 0.9rem;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .action-btn:hover {{
            background: #1d4ed8;
            transform: translateY(-1px);
        }}
        .action-btn.clear-btn {{
            background: #ef4444;
        }}
        .action-btn.clear-btn:hover {{
            background: #dc2626;
        }}
        .todo-item.active {{
            /* Active todo - no special styling */
        }}
        .code {{
            font-family: 'Courier New', monospace;
            background: #f1f5f9;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-size: 0.9rem;
        }}
        .page-nav {{
            margin: 2rem 0;
            padding: 1rem;
            background: #f8fafc;
            border-radius: 6px;
            text-align: center;
        }}
        .page-link {{
            color: #2563eb;
            font-weight: 600;
            text-decoration: none;
            border-bottom: 2px solid transparent;
        }}
        .page-link:hover {{
            border-bottom-color: #2563eb;
        }}
    </style>
</head>
<body>
    <div id="root">{content_html}</div>
    <script type="module" src="/static/bootstrap.js"></script>
</body>
</html>"""

    return shell

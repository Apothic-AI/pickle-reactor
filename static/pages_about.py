# ANCHOR: pages.about
# TITLE: About page component
# ROLE: pages/components layer
# SEE: server.app.routes, shared.vdom, client.router

"""
About page component for pickle-reactor framework.

Phase 4: Routing & Multiple Pages
- Demonstrates multi-page navigation
- Shows framework features and capabilities
- Includes navigation links to other pages

This demonstrates the routing pattern:
- Page components are registered in server routing registry
- Server renders correct page based on URL path
- Client-side router intercepts link clicks (MVP: full reload)
- Browser back/forward buttons work (MVP: via page reload)
"""

from shared.vdom import div, h1, h2, p, a, ul, li, span


def AboutPage(props: dict):
    """About page component describing the Pickle-Reactor framework.

    Phase 4 Features:
    - Static informational page
    - Navigation links to other pages
    - Demonstrates file-based routing

    Args:
        props: Component properties (currently unused)

    Returns:
        VNode tree representing the about page

    SEE: server.app.routes, pages.index.IndexPage, pages.todos.TodosPage
    """
    return div({"class": "container"},
        # Navigation
        div({"class": "nav"},
            a({"href": "/", "class": "nav-link"}, "Home"),
            span({}, " | "),
            a({"href": "/about", "class": "nav-link active"}, "About"),
            span({}, " | "),
            a({"href": "/todos", "class": "nav-link"}, "Todos"),
        ),

        # Header
        h1({"class": "title"}, "About Pickle-Reactor"),

        # Introduction
        p({"class": "subtitle"},
            "A ",
            span({"class": "highlight"}, "Next.js-style"),
            " Python framework using ",
            span({"class": "highlight"}, "Pyodide"),
            " and ",
            span({"class": "highlight"}, "VDOM diffing"),
            "."
        ),

        # Features
        div({"class": "section"},
            h2({}, "✨ Features"),
            ul({"class": "features-list"},
                li({}, "🐍 Write UI components in Python (server & client)"),
                li({}, "⚡ Server-Side Rendering (SSR) for fast initial load"),
                li({}, "🔄 Virtual DOM with efficient diffing algorithm"),
                li({}, "🎯 React-style hooks (use_state) for state management"),
                li({}, "🗺️ File-based routing (Next.js-style)"),
                li({}, "🔐 HTML escaping for XSS protection"),
                li({}, "🌐 Runs Python in browser via Pyodide WebAssembly"),
                li({}, "🎨 Component-based architecture"),
            )
        ),

        # Architecture
        div({"class": "section"},
            h2({}, "🏗️ Architecture"),
            p({},
                "Pickle-Reactor uses a hybrid rendering approach:"
            ),
            ul({"class": "architecture-list"},
                li({},
                    span({"class": "highlight"}, "Server (FastAPI): "),
                    "Renders components to HTML for initial page load"
                ),
                li({},
                    span({"class": "highlight"}, "Client (Pyodide): "),
                    "Hydrates HTML with interactivity using Python in WebAssembly"
                ),
                li({},
                    span({"class": "highlight"}, "VDOM: "),
                    "Efficient DOM updates using Preact-style O(n) diffing"
                ),
                li({},
                    span({"class": "highlight"}, "State: "),
                    "React-style hooks for component state management"
                ),
                li({},
                    span({"class": "highlight"}, "Routing: "),
                    "File-based routing with server and client-side navigation"
                ),
            )
        ),

        # Technology Stack
        div({"class": "section"},
            h2({}, "🛠️ Technology Stack"),
            ul({"class": "tech-list"},
                li({},
                    span({"class": "tech-name"}, "Pyodide 0.24+: "),
                    "Python 3.11 in WebAssembly"
                ),
                li({},
                    span({"class": "tech-name"}, "FastAPI: "),
                    "Modern async Python web framework"
                ),
                li({},
                    span({"class": "tech-name"}, "PyScript pydom: "),
                    "Pythonic DOM manipulation"
                ),
                li({},
                    span({"class": "tech-name"}, "VDOM: "),
                    "Custom Python implementation with Preact-style diffing"
                ),
                li({},
                    span({"class": "tech-name"}, "pytest: "),
                    "Comprehensive testing (unit, integration, E2E)"
                ),
            )
        ),

        # Implementation Phases
        div({"class": "section"},
            h2({}, "🚀 Implementation Phases"),
            ul({"class": "phases-list"},
                li({"class": "phase-complete"},
                    "✅ Phase 1: VNode, SSR, Pyodide Bootstrap"
                ),
                li({"class": "phase-complete"},
                    "✅ Phase 2: ComponentInstance, use_state, mount/rerender"
                ),
                li({"class": "phase-complete"},
                    "✅ Phase 3: patch(), events, keyed children"
                ),
                li({"class": "phase-complete"},
                    "✅ Phase 4: Routing, multiple pages"
                ),
                li({"class": "phase-complete"},
                    "✅ Phase 5: Data loading, server actions"
                ),
                li({"class": "phase-complete"},
                    "✅ Phase 6: CLI, Vite, hot reload"
                ),
            )
        ),

        # Call to Action
        div({"class": "cta"},
            p({},
                "Ready to build interactive Python web apps? ",
                a({"href": "/todos", "class": "cta-link"}, "Try the Todo demo"),
                " or ",
                a({"href": "/", "class": "cta-link"}, "go back home"),
                "!"
            )
        ),
    )

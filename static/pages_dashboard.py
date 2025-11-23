# ANCHOR: pages.dashboard
# TITLE: Dashboard page with SSR data loading and client refresh
# ROLE: pages/components layer
# SEE: server.app.routes, server.actions, client.actions, shared.state

"""
Dashboard page component for pickle-reactor framework.

Phase 5: Data Loading & Server Actions
This demonstrates:
- Server-side data loading (initial props from SSR)
- Client-side data refresh via fetch
- Async state management with use_state
- Loading states during async operations
- Error handling for network failures

ARCHITECTURE:
- SSR: Server passes initial data as props → fast first load
- Client: Component can refresh data via client.actions → interactive updates
- State: use_state tracks stats, loading state, errors

SEE: server.app.route_handler (loads initial data), client.actions.get_todos
"""

from shared.vdom import div, h1, h2, p, button, span, a
from shared.state import use_state
import asyncio


def DashboardPage(props: dict):
    """Dashboard page showing todo statistics.

    Phase 5 Features:
    - Displays todo statistics (total, done, active)
    - Initial data from SSR (props["data"])
    - Refresh button fetches fresh data from server
    - Loading state during async fetch
    - Navigation links to other pages

    Args:
        props: Component properties
            - data: Initial stats from SSR {"total": N, "done": N, "active": N}

    Returns:
        VNode tree representing the dashboard page

    SEE: server.app.route_handler, client.actions.get_todos
    """
    # Initial data from SSR (passed as props)
    initial_data = props.get('data', {'total': 0, 'done': 0, 'active': 0})

    # State: Current statistics
    stats, set_stats = use_state(initial_data)

    # State: Loading indicator
    loading, set_loading = use_state(False)

    # State: Error message
    error, set_error = use_state(None)

    async def refresh_data():
        """Fetch fresh data from server.

        WHY: Demonstrate client-side data loading

        Side effects:
            - Sets loading state
            - Makes async fetch request
            - Updates stats on success
            - Sets error message on failure

        SEE: client.actions.get_todos
        """
        set_loading(True)
        set_error(None)

        try:
            # Import client actions (only available in browser/Pyodide)
            from client.actions import get_todos

            # Fetch todos
            todos = await get_todos()

            # Calculate stats
            new_stats = {
                'total': len(todos),
                'done': sum(1 for t in todos if t['done']),
                'active': sum(1 for t in todos if not t['done']),
            }
            set_stats(new_stats)

        except Exception as e:
            # Handle errors (network failures, server errors)
            error_msg = f"Failed to load data: {str(e)}"
            set_error(error_msg)
            print(f"❌ {error_msg}")

        finally:
            set_loading(False)

    def handle_refresh(event):
        """Handle refresh button click.

        WHY: Trigger async data refresh

        NOTE: asyncio.create_task() schedules coroutine without blocking
        """
        # Create task to run async function
        asyncio.create_task(refresh_data())

    # Build UI
    return div({"class": "container"},
        # Navigation
        div({"class": "nav"},
            a({"href": "/", "class": "nav-link"}, "Home"),
            span({}, " | "),
            a({"href": "/about", "class": "nav-link"}, "About"),
            span({}, " | "),
            a({"href": "/todos", "class": "nav-link"}, "Todos"),
            span({}, " | "),
            a({"href": "/dashboard", "class": "nav-link active"}, "Dashboard"),
        ),

        # Header
        h1({"class": "title"}, "📊 Dashboard"),

        p({"class": "subtitle"},
            "Real-time todo statistics with ",
            span({"class": "highlight"}, "SSR data loading"),
            " and ",
            span({"class": "highlight"}, "client-side refresh"),
            "."
        ),

        # Statistics cards
        div({"class": "todo-stats"},
            div({"class": "stat"},
                span({"class": "stat-number"}, str(stats['total'])),
                span({"class": "stat-label"}, " total todos")
            ),
            div({"class": "stat"},
                span({"class": "stat-number"}, str(stats['done'])),
                span({"class": "stat-label"}, " completed")
            ),
            div({"class": "stat"},
                span({"class": "stat-number"}, str(stats['active'])),
                span({"class": "stat-label"}, " active")
            ),
        ),

        # Refresh button
        div({"class": "todo-actions"},
            button(
                {
                    "on_click": handle_refresh,
                    "class": "action-btn",
                    "id": "refresh-btn",
                    "disabled": loading
                },
                "🔄 Refresh Data" if not loading else "⏳ Loading..."
            ),
        ),

        # Error message
        (div({"class": "status"},
            p({}, f"❌ Error: {error}")
        ) if error else None),

        # Info section
        div({"class": "section"},
            h2({}, "How it works"),
            p({},
                "💡 ",
                span({"class": "highlight"}, "Server-Side Rendering (SSR): "),
                "When you first load this page, the server fetches todo data and passes it as ",
                span({"class": "code"}, "props"),
                " to the component. This provides fast initial load and SEO benefits."
            ),
            p({},
                "🔄 ",
                span({"class": "highlight"}, "Client-Side Refresh: "),
                "Click the Refresh button to fetch fresh data from the server using the ",
                span({"class": "code"}, "client.actions"),
                " module. This demonstrates async data loading in Pyodide."
            ),
            p({},
                "🎯 ",
                span({"class": "highlight"}, "Loading States: "),
                "The component tracks loading state and disables the button during fetch operations. ",
                "Errors are caught and displayed to the user."
            ),
        ),

        # Navigation links
        div({"class": "page-nav"},
            p({},
                "Try modifying todos on the ",
                a({"href": "/todos", "class": "page-link"}, "Todos page"),
                " then come back and refresh this dashboard to see updated stats!"
            )
        ),
    )

# ANCHOR: pages.index
# TITLE: Example index page component with interactive counter and todo list
# ROLE: pages/components layer
# SEE: server.app.home, shared.vdom, shared.state

"""
Example index page component for pickle-reactor framework.

Phase 3 enhancement:
- Demonstrates use_state hook for interactive components
- Counter demo (from Phase 2)
- Todo list demo with keyed children (Phase 3)
- Add/remove/toggle operations demonstrate efficient VDOM diffing

This demonstrates the component pattern:
- Components are Python callables that take props dict
- Return VNode trees using HTML helpers
- Can use hooks like use_state for interactivity
- Keyed children optimize dynamic list rendering
- Can be rendered on server (SSR) or client (Pyodide)
"""

from shared.vdom import div, h1, h2, p, button, span, ul, li, a
from shared.state import use_state


def IndexPage(props: dict):
    """Index page component with interactive counter and todo list.

    Phase 3 Features:
    - use_state hook for counter and todos state
    - Button click handlers for all interactions
    - Keyed children for efficient todo list rendering
    - Add/remove/toggle operations demonstrate patch() algorithm

    Args:
        props: Component properties (currently unused)

    Returns:
        VNode tree representing the page

    SEE: server.app.home, shared.vdom.div, shared.state.use_state, client.runtime.patch
    """
    # Phase 2: Interactive counter with use_state hook
    count, set_count = use_state(0)

    # Phase 3: Todo list with keyed children
    todos, set_todos = use_state([
        {"id": 1, "text": "Learn Pyodide", "done": False},
        {"id": 2, "text": "Build VDOM", "done": True},
        {"id": 3, "text": "Add diffing", "done": False}
    ])

    def handle_increment(event):
        """Increment counter on button click.

        WHY: Demonstrate state updates and re-rendering

        SEE: shared.state.use_state, client.runtime.rerender
        """
        set_count(count + 1)

    def add_todo(event):
        """Add new todo item to list.

        WHY: Demonstrate keyed children reconciliation with additions

        SEE: client.runtime.patch_keyed_children
        """
        new_todo = {"id": count + 100, "text": f"New task {count}", "done": False}
        set_todos(todos + [new_todo])
        set_count(count + 1)

    def toggle_todo(todo_id):
        """Create toggle handler for specific todo.

        WHY: Demonstrate keyed children reconciliation with updates

        Args:
            todo_id: ID of todo to toggle

        Returns:
            Event handler function
        """
        def handler(event):
            new_todos = [
                {**t, "done": not t["done"]} if t["id"] == todo_id else t
                for t in todos
            ]
            set_todos(new_todos)
        return handler

    def remove_todo(todo_id):
        """Create remove handler for specific todo.

        WHY: Demonstrate keyed children reconciliation with deletions

        Args:
            todo_id: ID of todo to remove

        Returns:
            Event handler function
        """
        def handler(event):
            new_todos = [t for t in todos if t["id"] != todo_id]
            set_todos(new_todos)
        return handler

    # Build todo list items with keys
    todo_items = [
        li(
            {
                "key": str(t["id"]),
                "class": "todo-item " + ("done" if t["done"] else "")
            },
            span({"class": "todo-text"}, t["text"]),
            button(
                {
                    "on_click": toggle_todo(t["id"]),
                    "class": "todo-toggle"
                },
                "✓" if not t["done"] else "↶"
            ),
            button(
                {
                    "on_click": remove_todo(t["id"]),
                    "class": "todo-remove"
                },
                "×"
            )
        )
        for t in todos
    ]

    return div({"class": "container"},
        # Phase 4: Navigation
        div({"class": "nav"},
            a({"href": "/", "class": "nav-link active"}, "Home"),
            span({}, " | "),
            a({"href": "/about", "class": "nav-link"}, "About"),
            span({}, " | "),
            a({"href": "/todos", "class": "nav-link"}, "Todos"),
        ),

        h1({"class": "title"}, "Welcome to Pickle-Reactor"),
        p({"class": "subtitle"},
            "A Next.js-style Python framework using ",
            span({"class": "highlight"}, "Pyodide"),
            " and ",
            span({"class": "highlight"}, "VDOM diffing")
        ),

        # Phase 2: Interactive Counter Demo
        div({"class": "counter-section"},
            h2({}, "🎯 Phase 2: Interactive Counter"),
            div({"class": "counter"},
                p({"class": "count-display", "id": "count"}, f"Count: {count}"),
                button(
                    {
                        "on_click": handle_increment,
                        "class": "increment-btn",
                        "id": "increment"
                    },
                    "➕ Increment"
                ),
                p({"class": "counter-info"},
                    "Click the button to increment the counter. "
                    "State updates trigger re-renders!"
                )
            )
        ),

        # Phase 3: Todo List Demo with Keyed Children
        div({"class": "todo-section"},
            h2({}, "📝 Phase 3: Todo List (Keyed Children)"),
            button(
                {
                    "on_click": add_todo,
                    "class": "add-todo-btn",
                    "id": "add-todo"
                },
                "➕ Add Todo"
            ),
            ul({"class": "todo-list", "id": "todo-list"}, *todo_items),
            p({"class": "todo-info"},
                "Add, toggle, or remove items. ",
                "Keyed children minimize DOM operations!"
            )
        ),

        div({"class": "features"},
            p({}, "✅ Server-Side Rendering (SSR)"),
            p({}, "✅ Python Components"),
            p({}, "✅ Virtual DOM"),
            p({}, "✅ HTML Escaping for Security"),
            p({}, "✅ use_state Hook (Phase 2)"),
            p({}, "✅ Interactive Event Handlers (Phase 2)"),
            p({}, "✅ Efficient VDOM Diffing (Phase 3)"),
            p({}, "✅ Keyed Children Reconciliation (Phase 3)")
        ),

        div({"class": "status", "id": "pyodide-status"},
            p({}, "⏳ Loading Pyodide...")
        )
    )

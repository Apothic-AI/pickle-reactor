# ANCHOR: pages.todos
# TITLE: Todos page component with full todo list functionality
# ROLE: pages/components layer
# SEE: server.app.routes, shared.vdom, shared.state, client.router

"""
Todos page component for pickle-reactor framework.

Phase 4: Routing & Multiple Pages
- Dedicated page for todo list functionality
- Demonstrates stateful components on separate routes
- Shows keyed children reconciliation with complex interactions

This demonstrates:
- File-based routing with stateful components
- use_state hook with complex state (list of objects)
- Keyed children for efficient list rendering
- Multiple event handlers with closures
- Navigation links between pages
"""

from shared.vdom import div, h1, h2, p, button, ul, li, input_, span, a
from shared.state import use_state


def TodosPage(props: dict):
    """Todos page component with full todo list functionality.

    Phase 4 Features:
    - Complete todo list with add/toggle/remove operations
    - Keyed children for efficient list reconciliation
    - Navigation to other pages
    - Demonstrates stateful routing

    Args:
        props: Component properties (currently unused)

    Returns:
        VNode tree representing the todos page

    SEE: server.app.routes, shared.state.use_state, client.runtime.patch_keyed_children
    """
    # State: List of todo items
    todos, set_todos = use_state([
        {"id": 1, "text": "Learn Pickle-Reactor", "done": False},
        {"id": 2, "text": "Build awesome Python web apps", "done": False},
        {"id": 3, "text": "Master Pyodide and VDOM", "done": True},
    ])

    # State: Counter for generating new todo IDs
    next_id, set_next_id = use_state(4)

    # State: Input text for new todo
    new_todo_text, set_new_todo_text = use_state("")

    def handle_input(event):
        """Handle input changes for new todo text.

        WHY: Track user input for new todo creation

        SEE: shared.state.use_state
        """
        # In Pyodide, event.target.value gives us the input value
        # For SSR, this is a no-op (events only work client-side)
        try:
            value = event.target.value if hasattr(event, 'target') else ""
            set_new_todo_text(value)
        except:
            pass

    def add_todo(event):
        """Add new todo item from input.

        WHY: Demonstrate keyed children reconciliation with additions

        SEE: client.runtime.patch_keyed_children
        """
        if new_todo_text.strip():
            new_todo = {
                "id": next_id,
                "text": new_todo_text.strip(),
                "done": False
            }
            set_todos(todos + [new_todo])
            set_next_id(next_id + 1)
            set_new_todo_text("")

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

    def clear_completed(event):
        """Remove all completed todos.

        WHY: Batch operation demonstrating multiple deletions at once
        """
        new_todos = [t for t in todos if not t["done"]]
        set_todos(new_todos)

    def toggle_all(event):
        """Toggle all todos between done/not done.

        WHY: Batch operation demonstrating multiple updates at once
        """
        # If all are done, mark all as not done; otherwise mark all as done
        all_done = all(t["done"] for t in todos) if todos else False
        new_todos = [{**t, "done": not all_done} for t in todos]
        set_todos(new_todos)

    # Calculate statistics
    total_count = len(todos)
    done_count = sum(1 for t in todos if t["done"])
    active_count = total_count - done_count

    # Build todo list items with keys
    todo_items = [
        li(
            {
                "key": str(t["id"]),
                "class": "todo-item " + ("done" if t["done"] else "active")
            },
            # Checkbox/toggle button
            button(
                {
                    "on_click": toggle_todo(t["id"]),
                    "class": "todo-toggle",
                    "title": "Mark as done" if not t["done"] else "Mark as active"
                },
                "✓" if not t["done"] else "↶"
            ),
            # Todo text
            span({"class": "todo-text"}, t["text"]),
            # Remove button
            button(
                {
                    "on_click": remove_todo(t["id"]),
                    "class": "todo-remove",
                    "title": "Remove todo"
                },
                "×"
            )
        )
        for t in todos
    ]

    return div({"class": "container"},
        # Navigation
        div({"class": "nav"},
            a({"href": "/", "class": "nav-link"}, "Home"),
            span({}, " | "),
            a({"href": "/about", "class": "nav-link"}, "About"),
            span({}, " | "),
            a({"href": "/todos", "class": "nav-link active"}, "Todos"),
        ),

        # Header
        h1({"class": "title"}, "📝 Todo List"),

        p({"class": "subtitle"},
            "A full-featured todo app demonstrating ",
            span({"class": "highlight"}, "stateful routing"),
            " and ",
            span({"class": "highlight"}, "keyed children reconciliation"),
            "."
        ),

        # Statistics
        div({"class": "todo-stats"},
            div({"class": "stat"},
                span({"class": "stat-number"}, str(total_count)),
                span({"class": "stat-label"}, " total")
            ),
            div({"class": "stat"},
                span({"class": "stat-number"}, str(active_count)),
                span({"class": "stat-label"}, " active")
            ),
            div({"class": "stat"},
                span({"class": "stat-number"}, str(done_count)),
                span({"class": "stat-label"}, " done")
            ),
        ),

        # Input for new todo
        div({"class": "todo-input-section"},
            input_(
                {
                    "type": "text",
                    "placeholder": "What needs to be done?",
                    "class": "todo-input",
                    "id": "new-todo-input",
                    "on_input": handle_input,
                    "value": new_todo_text
                }
            ),
            button(
                {
                    "on_click": add_todo,
                    "class": "add-todo-btn",
                    "id": "add-todo"
                },
                "➕ Add Todo"
            ),
        ),

        # Bulk actions
        div({"class": "todo-actions"},
            button(
                {
                    "on_click": toggle_all,
                    "class": "action-btn",
                    "id": "toggle-all"
                },
                "Toggle All"
            ),
            button(
                {
                    "on_click": clear_completed,
                    "class": "action-btn clear-btn",
                    "id": "clear-completed"
                },
                "Clear Completed"
            ),
        ),

        # Todo list
        ul({"class": "todo-list", "id": "todo-list"}, *todo_items),

        # Info
        div({"class": "todo-info"},
            p({},
                "💡 ",
                span({"class": "highlight"}, "Tip: "),
                "All state is managed locally in this component. ",
                "Navigate away and come back to reset the list!"
            ),
            p({},
                "🔍 ",
                span({"class": "highlight"}, "Under the hood: "),
                "Each todo has a unique ",
                span({"class": "code"}, "key"),
                " property. ",
                "When you add, remove, or reorder todos, the VDOM diffing algorithm ",
                "uses these keys to minimize DOM operations and reuse elements efficiently."
            ),
        ),

        # Navigation links
        div({"class": "page-nav"},
            p({},
                "Want to learn more? Check out the ",
                a({"href": "/about", "class": "page-link"}, "About page"),
                " or go back to the ",
                a({"href": "/", "class": "page-link"}, "Home page"),
                "."
            )
        ),
    )

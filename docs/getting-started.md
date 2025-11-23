# Getting Started with Pickle-Reactor

This guide will help you get up and running with Pickle-Reactor in under 5 minutes.

## Prerequisites

- Python 3.11 or higher
- Basic understanding of Python and web development
- Modern web browser (Chrome, Firefox, or Edge recommended)

## Installation

1. **Navigate to the pickle-reactor directory:**

```bash
cd experiments/pickle-reactor
```

2. **Install dependencies:**

```bash
# Using uv (recommended)
uv pip install -e ".[dev]"

# Or using pip
pip install -e ".[dev]"
```

3. **Verify installation:**

```bash
./pickle-reactor --help
```

You should see the CLI help output with available commands.

## Your First Component

Let's create a simple "Hello World" component.

### Step 1: Create a Page Component

Create a new file `pages/hello.py`:

```python
from shared.vdom import div, h1, p
from shared.state import use_state

def HelloPage(props):
    """
    A simple Hello World page with a counter.
    """
    count, set_count = use_state(0)

    return div(
        {"class": "container"},
        h1({}, "Hello, Pickle-Reactor! 🚀"),
        p({}, f"You've clicked the button {count} times"),
        button(
            {
                "on_click": lambda e: set_count(count + 1),
                "class": "btn"
            },
            "Click me!"
        )
    )
```

### Step 2: Register the Route

Open `server/app.py` and add your page to the ROUTES dictionary:

```python
from pages.hello import HelloPage

ROUTES = {
    "/": IndexPage,
    "/about": AboutPage,
    "/todos": TodosPage,
    "/hello": HelloPage,  # Add this line
}
```

### Step 3: Start Development Server

```bash
./pickle-reactor dev
```

You should see:

```
╔════════════════════════════════════════════╗
║    Pickle-Reactor Development Server       ║
╚════════════════════════════════════════════╝

🚀 Starting server on http://0.0.0.0:8000
📦 Hot reload enabled (watches Python files)
```

### Step 4: View in Browser

Open your browser to:

```
http://localhost:8000/hello
```

You should see your Hello World page with a working counter!

## Understanding Components

Let's break down the component we just created:

```python
def HelloPage(props):
    """Component function - takes props, returns VNode"""

    # State hook - returns (value, setter)
    count, set_count = use_state(0)

    # Return VNode tree
    return div(
        {"class": "container"},  # Props (attributes, events)
        h1({}, "Hello!"),         # Child 1
        p({}, f"Count: {count}"), # Child 2
        button(...)               # Child 3
    )
```

### Key Concepts

1. **Components are functions** - They take `props` and return a VNode tree
2. **State hooks** - `use_state(initial)` returns `(value, setter)` tuple
3. **VNodes** - Virtual DOM nodes created with `div()`, `h1()`, etc.
4. **Props** - First argument is dict of HTML attributes and event handlers
5. **Children** - Additional arguments are child VNodes or text strings
6. **Event handlers** - Use `on_*` prefix (e.g., `on_click`, `on_input`)

## Adding Styles

You can add inline styles to components:

```python
def StyledComponent(props):
    return div(
        {
            "class": "card",
            "style": {
                "backgroundColor": "#f0f0f0",
                "padding": "20px",
                "borderRadius": "8px"
            }
        },
        h2({"style": {"color": "#333"}}, "Styled Title"),
        p({}, "This is a styled component")
    )
```

Or reference external CSS in your server template (see `server/app.py`).

## Handling User Input

Create a form component with input handling:

```python
from shared.vdom import div, input, button, p

def FormExample(props):
    name, set_name = use_state("")
    email, set_email = use_state("")

    def handle_submit(e):
        print(f"Submitted: {name}, {email}")

    return div(
        {},
        input({
            "type": "text",
            "placeholder": "Name",
            "value": name,
            "on_input": lambda e: set_name(e.target.value)
        }),
        input({
            "type": "email",
            "placeholder": "Email",
            "value": email,
            "on_input": lambda e: set_email(e.target.value)
        }),
        button({"on_click": handle_submit}, "Submit"),
        p({}, f"Name: {name}, Email: {email}")
    )
```

## Creating a Todo List

Here's a more complete example - a todo list:

```python
from shared.vdom import div, h1, ul, li, input, button
from shared.state import use_state

def TodoListPage(props):
    todos, set_todos = use_state([])
    input_text, set_input_text = use_state("")

    def add_todo(e):
        if input_text.strip():
            new_todos = todos + [{"id": len(todos), "text": input_text, "done": False}]
            set_todos(new_todos)
            set_input_text("")

    def toggle_todo(todo_id):
        def handler(e):
            new_todos = [
                {**t, "done": not t["done"]} if t["id"] == todo_id else t
                for t in todos
            ]
            set_todos(new_todos)
        return handler

    def remove_todo(todo_id):
        def handler(e):
            new_todos = [t for t in todos if t["id"] != todo_id]
            set_todos(new_todos)
        return handler

    return div(
        {},
        h1({}, "My Todos"),
        div(
            {},
            input({
                "type": "text",
                "value": input_text,
                "on_input": lambda e: set_input_text(e.target.value),
                "placeholder": "Add a todo..."
            }),
            button({"on_click": add_todo}, "Add")
        ),
        ul(
            {},
            *[
                li(
                    {"key": str(todo["id"])},
                    input({
                        "type": "checkbox",
                        "checked": todo["done"],
                        "on_change": toggle_todo(todo["id"])
                    }),
                    span(
                        {"style": {"textDecoration": "line-through" if todo["done"] else "none"}},
                        todo["text"]
                    ),
                    button({"on_click": remove_todo(todo["id"])}, "×")
                )
                for todo in todos
            ]
        )
    )
```

## Hot Reload

Pickle-Reactor supports hot reload via uvicorn:

1. Start the dev server: `./pickle-reactor dev`
2. Edit any Python file (components, pages, etc.)
3. Save the file
4. Server automatically restarts
5. Refresh your browser (F5) to see changes

## Running Tests

Test your components:

```bash
# Run all tests
./pickle-reactor test

# Run only unit tests (fast)
./pickle-reactor test -m unit

# Run with verbose output
./pickle-reactor test -v
```

## Building for Production

When ready to deploy:

```bash
# Build production bundle
./pickle-reactor build

# Output will be in dist/ directory
cd dist
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

## Next Steps

- Read the [Component Guide](./components.md) for advanced patterns
- Learn about [State Management](./state.md) in depth
- Explore [Routing](./routing.md) for multi-page apps
- Study [Server Actions](./server-actions.md) for backend integration

## Troubleshooting

**Server won't start?**
- Check Python version: `python --version` (needs 3.11+)
- Install dependencies: `uv pip install -e ".[dev]"`
- Check port availability: port 8000 should be free

**Components not rendering?**
- Check browser console for errors (F12)
- Verify route is registered in `server/app.py`
- Check Pyodide loaded successfully (should see "Pyodide loaded" in console)

**State not updating?**
- Verify `use_state` called at component top level
- Check event handlers attached correctly
- Look for JavaScript errors in browser console

**Hot reload not working?**
- Server restarts automatically (watch terminal)
- Manually refresh browser (F5) after restart
- Check file watch permissions

## Resources

- [Main README](../README.md) - Comprehensive framework documentation
- [API Reference](./api.md) - Detailed API documentation
- [Examples](../pages/) - Example components and pages
- [RESEARCH.md](../RESEARCH.md) - Technical research and decisions

Happy building with Pickle-Reactor! 🚀

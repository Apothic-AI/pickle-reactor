# ANCHOR: client.actions
# TITLE: Client-side actions for calling server API
# ROLE: client/api layer
# EXPORTS: call_action, get_todos, create_todo, update_todo, delete_todo
# SEE: server.actions, pages.dashboard, tests.e2e.test-actions

"""
Client-side actions for pickle-reactor framework (runs in Pyodide).

Phase 5: Data Loading & Server Actions
This module provides Python wrappers around JavaScript fetch API:
- call_action(): Generic fetch wrapper with error handling
- get_todos(): Fetch all todos
- create_todo(): Create new todo
- update_todo(): Update todo status
- delete_todo(): Delete todo

IMPORTANT:
- This code runs in the browser via Pyodide (WebAssembly)
- Uses JavaScript fetch API via js module (Pyodide FFI)
- All network operations are async
- JSON serialization/deserialization handled by Python json module

SECURITY:
- Never send sensitive data without HTTPS in production
- All requests use JSON (never pickle)
- Server validates all payloads with Pydantic

PERFORMANCE:
- Network latency dominates (not Python execution time)
- fetch API handles caching, retries automatically
- Consider debouncing rapid-fire mutations
"""

import js  # Pyodide JavaScript FFI
import json
from pyodide.ffi import to_js


# ANCHOR: client.actions.call_action
# TITLE: Generic fetch wrapper with error handling
# ROLE: client/http layer
# SEE: client.actions.convenience-wrappers, server.actions.endpoints

async def call_action(method: str, path: str, data: dict = None):
    """Call a server action (API endpoint).

    Generic wrapper around JavaScript fetch API that:
    - Constructs fetch options with method, headers, body
    - Converts Python dict to JavaScript object
    - Handles JSON serialization/deserialization
    - Raises RuntimeError on network or server errors

    WHY: Centralize error handling and JSON conversion logic

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        path: API path (e.g., '/api/todos')
        data: Optional request body as dict

    Returns:
        Response data as dict (parsed JSON)

    Raises:
        RuntimeError: On network errors or non-2xx status codes

    Preconditions:
        - path starts with '/'
        - data is None or JSON-serializable dict

    Postconditions:
        - Returns parsed JSON response
        - Raises on any errors

    Side effects:
        - Makes HTTP request via JavaScript fetch
        - May modify server state (POST/PUT/DELETE)

    CALLERS: client.actions.convenience-wrappers, page components
    SEE: server.actions.endpoints, tests.e2e.test-actions
    """
    # Build fetch options
    options = {
        "method": method,
        "headers": {
            "Content-Type": "application/json",
        }
    }

    # Add body for mutations
    if data is not None:
        options["body"] = json.dumps(data)

    try:
        # Convert Python dict to JavaScript object
        js_options = to_js(options, dict_converter=js.Object.fromEntries)

        # Call fetch
        response = await js.fetch(path, js_options)

        # Check status
        if not response.ok:
            error_text = await response.text()
            raise RuntimeError(f"Server error {response.status}: {error_text}")

        # Parse JSON
        result_text = await response.text()
        result = json.loads(result_text)

        return result

    except Exception as e:
        print(f"❌ Action failed: {e}")
        raise RuntimeError(f"Action failed: {e}")


# ANCHOR: client.actions.convenience-wrappers
# TITLE: Convenience wrappers for common operations
# ROLE: client/api layer
# SEE: client.actions.call_action, server.actions.endpoints

async def get_todos():
    """Fetch all todos from server.

    Phase 5: Data loading

    Request:
        GET /api/todos

    Returns:
        List of todo dicts: [{"id": 1, "text": "...", "done": false}, ...]

    SEE: server.actions.list_todos, pages.dashboard
    """
    result = await call_action("GET", "/api/todos")
    return result.get("todos", [])


async def create_todo(text: str):
    """Create a new todo.

    Phase 5: Server actions for mutations

    Request:
        POST /api/todos
        Body: {"text": "..."}

    Args:
        text: Todo text (non-empty string)

    Returns:
        Created todo dict: {"id": 4, "text": "...", "done": false}

    SEE: server.actions.create_todo
    """
    result = await call_action("POST", "/api/todos", {"text": text})
    return result.get("todo")


async def update_todo(todo_id: int, done: bool):
    """Update a todo's done status.

    Phase 5: Server actions for mutations

    Request:
        PUT /api/todos/{todo_id}
        Body: {"done": true/false}

    Args:
        todo_id: ID of todo to update
        done: New completion status

    Returns:
        Updated todo dict: {"id": 1, "text": "...", "done": true}

    SEE: server.actions.update_todo
    """
    result = await call_action("PUT", f"/api/todos/{todo_id}", {"done": done})
    return result.get("todo")


async def delete_todo(todo_id: int):
    """Delete a todo.

    Phase 5: Server actions for mutations

    Request:
        DELETE /api/todos/{todo_id}

    Args:
        todo_id: ID of todo to delete

    Returns:
        True on success

    SEE: server.actions.delete_todo
    """
    await call_action("DELETE", f"/api/todos/{todo_id}")
    return True

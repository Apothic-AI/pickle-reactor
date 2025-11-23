# ANCHOR: server.actions
# TITLE: Server actions API for data mutations
# ROLE: server/api layer
# EXPORTS: router (FastAPI APIRouter), CRUD endpoints for todos
# SEE: server.app, client.actions, tests.integration.test-actions

"""
Server actions for pickle-reactor framework.

Phase 5: Data Loading & Server Actions
This module provides RESTful API endpoints for data mutations:
- POST /api/todos: Create new todo
- PUT /api/todos/{todo_id}: Update todo
- DELETE /api/todos/{todo_id}: Delete todo
- GET /api/todos: List all todos

ARCHITECTURE:
- Uses FastAPI APIRouter for clean endpoint organization
- Pydantic models for request validation
- In-memory data store (demo; replace with database in production)
- Returns JSON responses with success status and data

SECURITY:
- Pydantic validates all request payloads
- 404 errors for invalid todo IDs
- JSON-only communication (never pickle)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any

# ANCHOR: server.actions.router
# Create API router with /api prefix
router = APIRouter(prefix="/api", tags=["actions"])


# ANCHOR: server.actions.models
# TITLE: Pydantic models for request validation
# ROLE: data validation layer
# SEE: server.actions.endpoints, tests.unit.test-actions-validation

class CreateTodoPayload(BaseModel):
    """Request payload for creating a todo.

    Validates:
    - text is non-empty string
    """
    text: str = Field(..., min_length=1, description="Todo text")


class UpdateTodoPayload(BaseModel):
    """Request payload for updating a todo.

    Validates:
    - done is boolean
    """
    done: bool = Field(..., description="Todo completion status")


class TodoResponse(BaseModel):
    """Response model for todo item.

    Ensures consistent response format.
    """
    id: int
    text: str
    done: bool


class TodoListResponse(BaseModel):
    """Response model for todo list.

    Wraps todos array in object for extensibility.
    """
    todos: List[TodoResponse]


# ANCHOR: server.actions.database
# TITLE: In-memory todo database
# ROLE: data storage layer
# NOTE: Replace with real database (PostgreSQL, MongoDB) in production

# In-memory data store (for demo; use DB in production)
_todos_db: List[Dict[str, Any]] = [
    {"id": 1, "text": "Learn Pickle-Reactor", "done": False},
    {"id": 2, "text": "Build VDOM diffing", "done": True},
    {"id": 3, "text": "Implement server actions", "done": False},
]
_next_id = 4


def _reset_database():
    """Reset database to initial state (for testing).

    WHY: Tests need clean state between runs

    SEE: tests.integration.conftest
    """
    global _todos_db, _next_id
    _todos_db = [
        {"id": 1, "text": "Learn Pickle-Reactor", "done": False},
        {"id": 2, "text": "Build VDOM diffing", "done": True},
        {"id": 3, "text": "Implement server actions", "done": False},
    ]
    _next_id = 4


# ANCHOR: server.actions.endpoints
# TITLE: RESTful API endpoints
# ROLE: http/api layer
# SEE: client.actions, tests.integration.test-actions

@router.post("/todos", response_model=Dict[str, Any])
async def create_todo(payload: CreateTodoPayload):
    """Create a new todo.

    Phase 5: Server actions for data mutations

    Request:
        POST /api/todos
        Content-Type: application/json
        Body: {"text": "New todo text"}

    Response:
        {"success": true, "todo": {"id": 4, "text": "New todo text", "done": false}}

    Args:
        payload: Validated CreateTodoPayload

    Returns:
        JSON with success status and created todo

    SEE: client.actions.create_todo, tests.integration.test-create-todo
    """
    global _next_id

    new_todo = {
        "id": _next_id,
        "text": payload.text,
        "done": False
    }
    _todos_db.append(new_todo)
    _next_id += 1

    return {"success": True, "todo": new_todo}


@router.put("/todos/{todo_id}", response_model=Dict[str, Any])
async def update_todo(todo_id: int, payload: UpdateTodoPayload):
    """Update a todo's done status.

    Phase 5: Server actions for data mutations

    Request:
        PUT /api/todos/1
        Content-Type: application/json
        Body: {"done": true}

    Response:
        {"success": true, "todo": {"id": 1, "text": "...", "done": true}}

    Args:
        todo_id: ID of todo to update
        payload: Validated UpdateTodoPayload

    Returns:
        JSON with success status and updated todo

    Raises:
        HTTPException 404: If todo not found

    SEE: client.actions.update_todo, tests.integration.test-update-todo
    """
    todo = next((t for t in _todos_db if t["id"] == todo_id), None)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    todo["done"] = payload.done
    return {"success": True, "todo": todo}


@router.delete("/todos/{todo_id}", response_model=Dict[str, Any])
async def delete_todo(todo_id: int):
    """Delete a todo.

    Phase 5: Server actions for data mutations

    Request:
        DELETE /api/todos/1

    Response:
        {"success": true}

    Args:
        todo_id: ID of todo to delete

    Returns:
        JSON with success status

    Raises:
        HTTPException 404: If todo not found

    SEE: client.actions.delete_todo, tests.integration.test-delete-todo
    """
    global _todos_db
    original_len = len(_todos_db)
    _todos_db = [t for t in _todos_db if t["id"] != todo_id]

    if len(_todos_db) == original_len:
        raise HTTPException(status_code=404, detail="Todo not found")

    return {"success": True}


@router.get("/todos", response_model=TodoListResponse)
async def list_todos():
    """List all todos.

    Phase 5: Data loading from server

    Request:
        GET /api/todos

    Response:
        {"todos": [{"id": 1, "text": "...", "done": false}, ...]}

    Returns:
        JSON with array of todos

    SEE: client.actions.get_todos, pages.dashboard, tests.integration.test-list-todos
    """
    return {"todos": _todos_db}

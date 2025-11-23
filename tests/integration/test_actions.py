# ANCHOR: tests.integration.actions
# TITLE: Integration tests for server actions API
# ROLE: testing/integration layer
# COVERS: server.actions endpoints, CRUD operations
# SCENARIOS: Create, read, update, delete todos; 404 errors; data persistence

"""
Integration tests for server actions API endpoints.

Phase 5: Data Loading & Server Actions
Tests complete HTTP request/response cycle for todos API:
- POST /api/todos: Create todo
- GET /api/todos: List todos
- PUT /api/todos/{id}: Update todo
- DELETE /api/todos/{id}: Delete todo
- Error handling (404, validation errors)
"""

import pytest
from httpx import AsyncClient, ASGITransport
from server.app import app
from server.actions import _reset_database


@pytest.fixture(autouse=True)
def reset_database():
    """Reset database before each test.

    WHY: Ensure clean state for each test

    SEE: server.actions._reset_database
    """
    _reset_database()


@pytest.fixture
async def client():
    """Create async test client with ASGITransport.

    WHY: httpx AsyncClient requires ASGITransport for ASGI apps

    SEE: tests.integration.test-server
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
class TestListTodos:
    """Test GET /api/todos endpoint."""

    async def test_list_todos_returns_initial_data(self, client):
        """List todos returns initial database state."""
        response = await client.get("/api/todos")

        assert response.status_code == 200
        data = response.json()

        assert "todos" in data
        assert isinstance(data["todos"], list)
        assert len(data["todos"]) == 3

        # Check initial todos
        assert data["todos"][0]["id"] == 1
        assert data["todos"][0]["text"] == "Learn Pickle-Reactor"
        assert data["todos"][0]["done"] is False

        assert data["todos"][1]["id"] == 2
        assert data["todos"][1]["text"] == "Build VDOM diffing"
        assert data["todos"][1]["done"] is True

    async def test_list_todos_empty_after_deletions(self, client):
        """List todos returns empty array after all deleted."""
        # Delete all todos
        await client.delete("/api/todos/1")
        await client.delete("/api/todos/2")
        await client.delete("/api/todos/3")

        response = await client.get("/api/todos")

        assert response.status_code == 200
        data = response.json()
        assert data["todos"] == []


@pytest.mark.asyncio
class TestCreateTodo:
    """Test POST /api/todos endpoint."""

    async def test_create_todo_success(self, client):
        """Create todo returns success with new todo."""
        response = await client.post(
            "/api/todos",
            json={"text": "New todo item"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "todo" in data

        todo = data["todo"]
        assert todo["id"] == 4  # Next ID after initial 3
        assert todo["text"] == "New todo item"
        assert todo["done"] is False

    async def test_create_todo_increments_id(self, client):
        """Each created todo gets unique incrementing ID."""
        resp1 = await client.post("/api/todos", json={"text": "Todo 1"})
        resp2 = await client.post("/api/todos", json={"text": "Todo 2"})

        data1 = resp1.json()
        data2 = resp2.json()

        assert data1["todo"]["id"] == 4
        assert data2["todo"]["id"] == 5

    async def test_create_todo_persists_in_list(self, client):
        """Created todo appears in list endpoint."""
        await client.post("/api/todos", json={"text": "Persisted todo"})
        list_response = await client.get("/api/todos")

        todos = list_response.json()["todos"]
        assert len(todos) == 4  # 3 initial + 1 new

        new_todo = next(t for t in todos if t["text"] == "Persisted todo")
        assert new_todo["id"] == 4
        assert new_todo["done"] is False

    async def test_create_todo_empty_text_validation_error(self, client):
        """Empty text triggers validation error."""
        response = await client.post("/api/todos", json={"text": ""})

        assert response.status_code == 422  # Validation error

    async def test_create_todo_missing_text_validation_error(self, client):
        """Missing text field triggers validation error."""
        response = await client.post("/api/todos", json={})

        assert response.status_code == 422


@pytest.mark.asyncio
class TestUpdateTodo:
    """Test PUT /api/todos/{id} endpoint."""

    async def test_update_todo_mark_done(self, client):
        """Update todo to mark as done."""
        response = await client.put(
            "/api/todos/1",
            json={"done": True}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["todo"]["id"] == 1
        assert data["todo"]["done"] is True
        assert data["todo"]["text"] == "Learn Pickle-Reactor"

    async def test_update_todo_mark_not_done(self, client):
        """Update todo to mark as not done."""
        response = await client.put(
            "/api/todos/2",  # Initially done=True
            json={"done": False}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["todo"]["id"] == 2
        assert data["todo"]["done"] is False

    async def test_update_todo_persists_in_list(self, client):
        """Updated todo status persists in list."""
        await client.put("/api/todos/1", json={"done": True})
        list_response = await client.get("/api/todos")

        todos = list_response.json()["todos"]
        todo1 = next(t for t in todos if t["id"] == 1)
        assert todo1["done"] is True

    async def test_update_todo_not_found(self, client):
        """Update non-existent todo returns 404."""
        response = await client.put(
            "/api/todos/999",
            json={"done": True}
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_update_todo_missing_done_field(self, client):
        """Update without done field triggers validation error."""
        response = await client.put("/api/todos/1", json={})

        assert response.status_code == 422


@pytest.mark.asyncio
class TestDeleteTodo:
    """Test DELETE /api/todos/{id} endpoint."""

    async def test_delete_todo_success(self, client):
        """Delete todo returns success."""
        response = await client.delete("/api/todos/1")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_delete_todo_removes_from_list(self, client):
        """Deleted todo no longer appears in list."""
        await client.delete("/api/todos/1")
        list_response = await client.get("/api/todos")

        todos = list_response.json()["todos"]
        assert len(todos) == 2  # 3 - 1
        assert not any(t["id"] == 1 for t in todos)

    async def test_delete_todo_not_found(self, client):
        """Delete non-existent todo returns 404."""
        response = await client.delete("/api/todos/999")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_delete_todo_multiple(self, client):
        """Delete multiple todos in sequence."""
        await client.delete("/api/todos/1")
        await client.delete("/api/todos/2")
        list_response = await client.get("/api/todos")

        todos = list_response.json()["todos"]
        assert len(todos) == 1
        assert todos[0]["id"] == 3


@pytest.mark.asyncio
class TestCRUDWorkflow:
    """Test complete CRUD workflow."""

    async def test_full_todo_lifecycle(self, client):
        """Complete workflow: create, read, update, delete."""
        # Create
        create_resp = await client.post(
            "/api/todos",
            json={"text": "Lifecycle test todo"}
        )
        todo_id = create_resp.json()["todo"]["id"]

        # Read (list)
        list_resp = await client.get("/api/todos")
        todos = list_resp.json()["todos"]
        assert any(t["id"] == todo_id for t in todos)

        # Update
        update_resp = await client.put(
            f"/api/todos/{todo_id}",
            json={"done": True}
        )
        assert update_resp.json()["todo"]["done"] is True

        # Delete
        delete_resp = await client.delete(f"/api/todos/{todo_id}")
        assert delete_resp.json()["success"] is True

        # Verify deleted
        final_list_resp = await client.get("/api/todos")
        final_todos = final_list_resp.json()["todos"]
        assert not any(t["id"] == todo_id for t in final_todos)

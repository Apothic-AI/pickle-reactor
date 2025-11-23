# ANCHOR: tests.integration.server-routing
# TITLE: Integration tests for server routing
# ROLE: testing/integration layer
# COVERS: server.app.route_handler, server.ssr, pages.*
# SEE: server.app, tests.unit.test-routing

"""
Integration tests for Phase 4 server-side routing.

Tests:
- Route handler returns 200 for valid routes
- Route handler returns 404 for unknown routes
- Correct component rendered per route
- Page component name embedded in HTML
- Page titles correct per route
- Navigation links present in all pages
"""

import pytest
from httpx import AsyncClient, ASGITransport
from server.app import app


@pytest.mark.asyncio
class TestServerRouting:
    """Test server route handler with httpx AsyncClient."""

    async def test_home_route_returns_200(self):
        """GET / returns 200 OK."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/")
            assert response.status_code == 200

    async def test_about_route_returns_200(self):
        """GET /about returns 200 OK."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/about")
            assert response.status_code == 200

    async def test_todos_route_returns_200(self):
        """GET /todos returns 200 OK."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/todos")
            assert response.status_code == 200

    async def test_unknown_route_returns_404(self):
        """GET /unknown returns 404 Not Found."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/unknown")
            assert response.status_code == 404

    async def test_nonexistent_route_returns_404(self):
        """GET /nonexistent returns 404 Not Found."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/nonexistent")
            assert response.status_code == 404


@pytest.mark.asyncio
class TestRouteContent:
    """Test content of server-rendered pages."""

    async def test_home_page_contains_welcome_title(self):
        """Home page contains 'Welcome to Pickle-Reactor' title."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/")
            assert "Welcome to Pickle-Reactor" in response.text

    async def test_about_page_contains_about_title(self):
        """About page contains 'About Pickle-Reactor' title."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/about")
            assert "About Pickle-Reactor" in response.text

    async def test_todos_page_contains_todo_title(self):
        """Todos page contains 'Todo List' title."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/todos")
            assert "Todo List" in response.text


@pytest.mark.asyncio
class TestPageComponentEmbedding:
    """Test that page component name is embedded in HTML for client hydration."""

    async def test_home_page_embeds_index_page_component(self):
        """Home page embeds IndexPage component name in script tag."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/")
            assert "window.__PAGE_COMPONENT__ = 'IndexPage'" in response.text

    async def test_about_page_embeds_about_page_component(self):
        """About page embeds AboutPage component name in script tag."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/about")
            assert "window.__PAGE_COMPONENT__ = 'AboutPage'" in response.text

    async def test_todos_page_embeds_todos_page_component(self):
        """Todos page embeds TodosPage component name in script tag."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/todos")
            assert "window.__PAGE_COMPONENT__ = 'TodosPage'" in response.text


@pytest.mark.asyncio
class TestPageTitles:
    """Test that page titles are correct per route."""

    async def test_home_page_title(self):
        """Home page has correct title in <title> tag."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/")
            assert "<title>Pickle-Reactor Framework</title>" in response.text

    async def test_about_page_title(self):
        """About page has correct title in <title> tag."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/about")
            assert "<title>About - Pickle-Reactor</title>" in response.text

    async def test_todos_page_title(self):
        """Todos page has correct title in <title> tag."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/todos")
            assert "<title>Todos - Pickle-Reactor</title>" in response.text


@pytest.mark.asyncio
class TestNavigationLinks:
    """Test that navigation links are present in all pages."""

    async def test_home_page_has_navigation(self):
        """Home page has navigation links to all pages."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/")
            # Check for navigation links
            assert 'href="/"' in response.text
            assert 'href="/about"' in response.text
            assert 'href="/todos"' in response.text

    async def test_about_page_has_navigation(self):
        """About page has navigation links to all pages."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/about")
            assert 'href="/"' in response.text
            assert 'href="/about"' in response.text
            assert 'href="/todos"' in response.text

    async def test_todos_page_has_navigation(self):
        """Todos page has navigation links to all pages."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/todos")
            assert 'href="/"' in response.text
            assert 'href="/about"' in response.text
            assert 'href="/todos"' in response.text


@pytest.mark.asyncio
class Test404Response:
    """Test 404 error response structure."""

    async def test_404_response_is_json(self):
        """404 response returns JSON error."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/unknown")
            assert response.status_code == 404
            data = response.json()
            assert "error" in data
            assert data["error"] == "Page not found"

    async def test_404_response_includes_path(self):
        """404 response includes the requested path."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/unknown")
            data = response.json()
            assert "path" in data
            assert data["path"] == "/unknown"

    async def test_404_response_includes_available_routes(self):
        """404 response includes list of available routes."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/unknown")
            data = response.json()
            assert "available_routes" in data
            assert isinstance(data["available_routes"], list)
            assert "/" in data["available_routes"]
            assert "/about" in data["available_routes"]
            assert "/todos" in data["available_routes"]


@pytest.mark.asyncio
class TestHTMLStructure:
    """Test HTML structure and required elements."""

    async def test_all_pages_have_root_div(self):
        """All pages have root div with id='root'."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for path in ["/", "/about", "/todos"]:
                response = await client.get(path)
                assert '<div id="root">' in response.text

    async def test_all_pages_load_pyodide(self):
        """All pages load Pyodide from CDN."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for path in ["/", "/about", "/todos"]:
                response = await client.get(path)
                assert "pyodide.js" in response.text

    async def test_all_pages_load_bootstrap(self):
        """All pages load bootstrap.js."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for path in ["/", "/about", "/todos"]:
                response = await client.get(path)
                assert "/static/bootstrap.js" in response.text


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Test health check endpoint."""

    async def test_health_endpoint_returns_200(self):
        """GET /health returns 200 OK."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200

    async def test_health_endpoint_returns_json(self):
        """GET /health returns JSON."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            data = response.json()
            assert "status" in data
            assert data["status"] == "ok"

    async def test_health_endpoint_phase_4(self):
        """GET /health reports phase 4."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            data = response.json()
            assert "phase" in data
            assert data["phase"] == "4"

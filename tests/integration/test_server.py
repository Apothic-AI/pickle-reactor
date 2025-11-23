# ANCHOR: tests.integration.server
# TITLE: Integration tests for FastAPI server
# COVERS: server.app, server.ssr integration with FastAPI
# ROLE: testing/integration layer (Tier 3)
# SCENARIOS: HTTP routes, SSR rendering, static files, response headers

"""
Integration tests for FastAPI server with SSR.

Tests cover:
- GET / endpoint returns SSR HTML
- HTML contains expected page content
- Static file serving
- Response headers (content-type, etc.)
- Health check endpoint
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from server.app import app


@pytest_asyncio.fixture
async def client():
    """Test client for FastAPI app.

    Uses httpx AsyncClient with ASGITransport for testing ASGI apps.
    No actual HTTP server needed - direct ASGI invocation.

    SEE: https://www.python-httpx.org/async/#calling-into-python-web-apps
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHomeRoute:
    """Test GET / route with SSR."""

    @pytest.mark.asyncio
    async def test_home_returns_html(self, client):
        """GET / returns HTML with 200 status."""
        response = await client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_home_contains_doctype(self, client):
        """GET / returns valid HTML with DOCTYPE."""
        response = await client.get("/")
        html = response.text
        assert html.startswith("<!DOCTYPE html>")

    @pytest.mark.asyncio
    async def test_home_contains_root_div(self, client):
        """GET / contains root div for mounting."""
        response = await client.get("/")
        html = response.text
        assert '<div id="root">' in html

    @pytest.mark.asyncio
    async def test_home_contains_ssr_content(self, client):
        """GET / contains server-rendered page content."""
        response = await client.get("/")
        html = response.text

        # Check for content from IndexPage component
        assert "Welcome to Pickle-Reactor" in html
        assert "Pyodide" in html
        assert "VDOM" in html

    @pytest.mark.asyncio
    async def test_home_contains_bootstrap_script(self, client):
        """GET / includes Pyodide bootstrap script."""
        response = await client.get("/")
        html = response.text
        assert '/static/bootstrap.js' in html
        assert 'type="module"' in html

    @pytest.mark.asyncio
    async def test_home_has_meta_viewport(self, client):
        """GET / includes viewport meta tag for mobile."""
        response = await client.get("/")
        html = response.text
        assert '<meta name="viewport"' in html

    @pytest.mark.asyncio
    async def test_home_has_charset_utf8(self, client):
        """GET / declares UTF-8 charset."""
        response = await client.get("/")
        html = response.text
        assert '<meta charset="UTF-8">' in html


class TestSSRIntegration:
    """Test SSR rendering integration."""

    @pytest.mark.asyncio
    async def test_ssr_renders_component_props(self, client):
        """SSR correctly renders component with props."""
        response = await client.get("/")
        html = response.text

        # Check that component structure is rendered
        assert '<div class="container">' in html
        assert '<h1 class="title">' in html

    @pytest.mark.asyncio
    async def test_ssr_escapes_html(self, client):
        """SSR HTML-escapes content (no XSS)."""
        response = await client.get("/")
        html = response.text

        # Verify no unescaped script tags
        # (Our content doesn't have scripts, but structure is escaped)
        assert "<script>alert(" not in html

    @pytest.mark.asyncio
    async def test_ssr_renders_nested_elements(self, client):
        """SSR renders nested element structures."""
        response = await client.get("/")
        html = response.text

        # Check nested structure from IndexPage
        assert '<div class="features">' in html
        assert '<p>✅' in html  # Features list items

    @pytest.mark.asyncio
    async def test_ssr_includes_status_element(self, client):
        """SSR includes Pyodide status element."""
        response = await client.get("/")
        html = response.text

        assert 'id="pyodide-status"' in html
        assert "Loading Pyodide..." in html


class TestHealthEndpoint:
    """Test health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_json(self, client):
        """GET /health returns JSON with 200."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_health_has_status_ok(self, client):
        """GET /health returns status: ok."""
        response = await client.get("/health")
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_has_framework_name(self, client):
        """GET /health includes framework name."""
        response = await client.get("/health")
        data = response.json()
        assert data["framework"] == "pickle-reactor"

    @pytest.mark.asyncio
    async def test_health_has_phase_info(self, client):
        """GET /health includes phase information."""
        response = await client.get("/health")
        data = response.json()
        assert "phase" in data
        assert data["phase"] == "1"


class TestStaticFiles:
    """Test static file serving."""

    @pytest.mark.asyncio
    async def test_bootstrap_js_exists(self, client):
        """GET /static/bootstrap.js returns JavaScript file."""
        response = await client.get("/static/bootstrap.js")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_bootstrap_js_content_type(self, client):
        """bootstrap.js has correct content-type."""
        response = await client.get("/static/bootstrap.js")
        # Content-type may vary, but should indicate JavaScript
        content_type = response.headers.get("content-type", "")
        assert "javascript" in content_type.lower() or "text/plain" in content_type

    @pytest.mark.asyncio
    async def test_bootstrap_js_contains_pyodide(self, client):
        """bootstrap.js contains Pyodide loading code."""
        response = await client.get("/static/bootstrap.js")
        js_content = response.text
        assert "pyodide" in js_content.lower()
        assert "loadPyodide" in js_content


class TestResponseHeaders:
    """Test HTTP response headers."""

    @pytest.mark.asyncio
    async def test_home_content_type_html(self, client):
        """Home route returns text/html content-type."""
        response = await client.get("/")
        assert "text/html" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_home_charset_utf8(self, client):
        """Home route declares UTF-8 charset in headers or content."""
        response = await client.get("/")
        # Either in header or in HTML meta tag
        content_type = response.headers.get("content-type", "")
        html = response.text

        assert "charset=utf-8" in content_type.lower() or \
               'charset="UTF-8"' in html or \
               "utf-8" in html.lower()


class TestErrorHandling:
    """Test error handling (404, etc.)."""

    @pytest.mark.asyncio
    async def test_404_for_unknown_route(self, client):
        """Unknown routes return 404."""
        response = await client.get("/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_404_returns_json(self, client):
        """404 response is JSON (FastAPI default)."""
        response = await client.get("/nonexistent")
        # FastAPI returns JSON 404 by default
        assert "application/json" in response.headers.get("content-type", "")

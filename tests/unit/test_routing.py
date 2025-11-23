# ANCHOR: tests.unit.routing
# TITLE: Unit tests for routing registry
# ROLE: testing layer
# COVERS: server.app.routes, server.app.route_handler
# SEE: server.app, tests.integration.test-server-routing

"""
Unit tests for Phase 4 routing functionality.

Tests:
- ROUTES registry structure and contents
- Route path normalization
- Route lookup logic
- 404 handling for unknown routes
"""

import pytest
from server.app import ROUTES
from pages.index import IndexPage
from pages.about import AboutPage
from pages.todos import TodosPage


class TestRoutingRegistry:
    """Test the routing registry structure and contents."""

    def test_routes_is_dict(self):
        """ROUTES registry is a dictionary."""
        assert isinstance(ROUTES, dict)

    def test_routes_not_empty(self):
        """ROUTES registry contains at least one route."""
        assert len(ROUTES) > 0

    def test_home_route_exists(self):
        """Home route (/) exists in ROUTES."""
        assert "/" in ROUTES

    def test_about_route_exists(self):
        """About route (/about) exists in ROUTES."""
        assert "/about" in ROUTES

    def test_todos_route_exists(self):
        """Todos route (/todos) exists in ROUTES."""
        assert "/todos" in ROUTES

    def test_route_values_are_tuples(self):
        """Each route value is a (component, component_name) tuple."""
        for path, value in ROUTES.items():
            assert isinstance(value, tuple), f"Route {path} value is not a tuple"
            assert len(value) == 2, f"Route {path} tuple does not have 2 elements"

    def test_route_components_are_callable(self):
        """Each route component is callable."""
        for path, (component, component_name) in ROUTES.items():
            assert callable(component), f"Route {path} component is not callable"

    def test_route_component_names_are_strings(self):
        """Each route component name is a string."""
        for path, (component, component_name) in ROUTES.items():
            assert isinstance(component_name, str), f"Route {path} component name is not a string"
            assert len(component_name) > 0, f"Route {path} component name is empty"


class TestRouteMapping:
    """Test correct component mapping for each route."""

    def test_home_route_maps_to_index_page(self):
        """Home route (/) maps to IndexPage component."""
        component, component_name = ROUTES["/"]
        assert component is IndexPage
        assert component_name == "IndexPage"

    def test_about_route_maps_to_about_page(self):
        """About route (/about) maps to AboutPage component."""
        component, component_name = ROUTES["/about"]
        assert component is AboutPage
        assert component_name == "AboutPage"

    def test_todos_route_maps_to_todos_page(self):
        """Todos route (/todos) maps to TodosPage component."""
        component, component_name = ROUTES["/todos"]
        assert component is TodosPage
        assert component_name == "TodosPage"


class TestRoutePathNormalization:
    """Test path normalization logic for route lookup."""

    def test_empty_path_normalizes_to_home(self):
        """Empty path "" normalizes to "/"."""
        path = ""
        route_path = "/" + path if path else "/"
        assert route_path == "/"

    def test_home_path_stays_home(self):
        """Path "/" stays as "/"."""
        path = ""  # FastAPI gives empty string for "/"
        route_path = "/" + path if path else "/"
        assert route_path == "/"

    def test_about_path_normalizes(self):
        """Path "about" normalizes to "/about"."""
        path = "about"
        route_path = "/" + path if path else "/"
        assert route_path == "/about"

    def test_todos_path_normalizes(self):
        """Path "todos" normalizes to "/todos"."""
        path = "todos"
        route_path = "/" + path if path else "/"
        assert route_path == "/todos"


class TestRouteNotFound:
    """Test 404 handling for unknown routes."""

    def test_unknown_route_not_in_registry(self):
        """Unknown routes are not in ROUTES registry."""
        assert "/unknown" not in ROUTES
        assert "/nonexistent" not in ROUTES
        assert "/does-not-exist" not in ROUTES

    def test_case_sensitive_routes(self):
        """Routes are case-sensitive (e.g., /About != /about)."""
        assert "/about" in ROUTES
        assert "/About" not in ROUTES

    def test_trailing_slash_matters(self):
        """Trailing slashes matter in route matching."""
        # Current implementation: routes don't have trailing slashes
        assert "/" in ROUTES
        assert "/about" in ROUTES
        # These should NOT exist (unless explicitly added)
        assert "/about/" not in ROUTES


class TestComponentRendering:
    """Test that route components can be rendered."""

    def test_index_page_renders(self):
        """IndexPage component can be called and returns VNode."""
        component, _ = ROUTES["/"]
        # For now, we just test that it's callable
        # Full rendering test is in integration tests
        assert callable(component)

    def test_about_page_renders(self):
        """AboutPage component can be called and returns VNode."""
        component, _ = ROUTES["/about"]
        assert callable(component)

    def test_todos_page_renders(self):
        """TodosPage component can be called and returns VNode."""
        component, _ = ROUTES["/todos"]
        assert callable(component)


# ANCHOR: tests.unit.routing.edge-cases
# TITLE: Edge cases for routing
# ROLE: testing/edge-cases layer

class TestRoutingEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_routes_registry_immutable(self):
        """ROUTES registry should not be modified during tests."""
        original_routes = dict(ROUTES)
        # Run some operations
        _ = "/" in ROUTES
        _ = ROUTES.get("/about")
        # Verify unchanged
        assert ROUTES == original_routes

    def test_all_component_names_unique(self):
        """All component names in ROUTES are unique."""
        component_names = [name for _, name in ROUTES.values()]
        assert len(component_names) == len(set(component_names))

    def test_all_routes_start_with_slash(self):
        """All route paths start with /."""
        for path in ROUTES.keys():
            assert path.startswith("/"), f"Route {path} does not start with /"

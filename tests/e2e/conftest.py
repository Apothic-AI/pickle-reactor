# ANCHOR: tests.e2e.conftest
# TITLE: E2E test configuration and fixtures
# ROLE: testing/e2e infrastructure
# EXPORTS: pytest configuration, shared fixtures

"""
E2E test configuration for Playwright tests.

Provides:
- pytest-asyncio configuration
- Shared fixtures for browser testing
- Test timeouts and retries
- Console logging helpers
"""

import pytest


def pytest_configure(config):
    """
    Configure pytest for E2E tests.

    WHY: Set up E2E-specific markers and configuration

    SEE: pytest documentation
    """
    config.addinivalue_line(
        "markers",
        "e2e: End-to-end browser tests (slow, requires server running)"
    )


@pytest.fixture(scope="session")
def event_loop_policy():
    """
    Use default event loop policy for E2E tests.

    WHY: Playwright requires proper async event loop

    SEE: pytest-asyncio documentation
    """
    import asyncio
    return asyncio.DefaultEventLoopPolicy()

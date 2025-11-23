# ANCHOR: server.ssr
# TITLE: Server-side rendering (SSR) implementation
# ROLE: server/rendering layer
# EXPORTS: render_to_string
# SEE: shared.vdom.VNode, server.app.home, tests.unit.test-ssr

"""
Server-Side Rendering (SSR) module for pickle-reactor framework.

This module provides render_to_string() function to convert VNode trees
into HTML strings for initial page load. Critical security feature: all
user-provided text content is HTML-escaped to prevent XSS attacks.

SECURITY:
- ALWAYS escapes text content with html.escape()
- Event handlers (on_*) are ignored on server (client-only)
- Attribute values are properly quoted and escaped

SEE: RESEARCH.md section 4 - Python SSR Frameworks
"""

from html import escape as esc
from typing import Union
from shared.vdom import VNode


def render_to_string(node: Union[VNode, str]) -> str:
    """Render VNode to HTML string with proper escaping.

    This function performs server-side rendering by converting a VNode tree
    into an HTML string. All text content is escaped to prevent XSS attacks.
    Event handlers (on_*) are ignored since they're client-side only.

    Args:
        node: VNode to render or plain text string

    Returns:
        HTML string representation

    INVARIANTS:
    - Always escapes user text content to prevent XSS
    - Event handlers (on_*) are ignored on server
    - Boolean props: True → attribute present, False/None → omitted
    - Attribute values are always quoted

    Security:
        - Text content is escaped with html.escape()
        - Attribute values are escaped
        - Never trust user input - always escape

    Examples:
        >>> render_to_string(div({}, "Hello"))
        '<div>Hello</div>'

        >>> render_to_string(div({}, "<script>alert('xss')</script>"))
        '<div>&lt;script&gt;alert('xss')&lt;/script&gt;</div>'

    SEE: shared.vdom.VNode, server.app.home, tests.unit.test-ssr
    """
    # Handle text nodes (strings)
    if isinstance(node, str):
        return esc(node)

    # Handle VNode
    tag = node.tag
    props = node.props or {}
    children = node.children or []

    # Build attributes from props
    # SECURITY: Event handlers (on_*) are ignored on server
    attr_parts = []
    for k, v in props.items():
        # Skip event handlers (client-side only)
        if k.startswith("on_"):
            continue

        # Handle boolean attributes
        if v is True:
            attr_parts.append(k)
        elif v is False or v is None:
            # Omit false/none attributes
            continue
        else:
            # Regular attribute with value
            # SECURITY: Escape attribute values
            attr_parts.append(f'{k}="{esc(str(v))}"')

    # Build attribute string
    attrs = (" " + " ".join(attr_parts)) if attr_parts else ""

    # Recursively render children
    inner = "".join(render_to_string(c) for c in children)

    # Return complete HTML element
    return f"<{tag}{attrs}>{inner}</{tag}>"

# ANCHOR: shared.vdom
# TITLE: Virtual DOM implementation with VNode and HTML helpers
# ROLE: vdom/representation layer
# EXPORTS: VNode, h, div, button, span, h1, p, input_field, and other HTML helpers
# SEE: server.ssr.render-to-string, client.runtime.mount, tests.unit.test-vdom

"""
Virtual DOM (VDOM) implementation for pickle-reactor framework.

This module provides:
- VNode dataclass: Virtual node representation with tag, props, children, and key
- h() function: Helper for creating VNodes
- HTML element helpers: div(), button(), span(), etc. for ergonomic component authoring

Inspired by htpy functional API with bracket notation support planned for Phase 2.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, Callable


# Type alias for VNode children (can be VNode or string)
VNodeChild = Union["VNode", str]


@dataclass
class VNode:
    """Virtual DOM node representation.

    INVARIANTS:
    - tag is non-empty string (HTML tag name)
    - props keys starting with "on_" are event handlers (callable)
    - children can contain VNodes or strings (text nodes)
    - key is optional; required for list reconciliation in phase 3

    Attributes:
        tag: HTML tag name (e.g., "div", "button")
        props: Dictionary of element properties and event handlers
        children: List of child VNodes or text strings
        key: Optional unique key for list reconciliation
        _el: Attached DOM element (client-side only, set by mount())

    SEE: shared.vdom.h, server.ssr.render-to-string, client.runtime.mount
    """
    tag: str
    props: Dict[str, Any] = field(default_factory=dict)
    children: List[VNodeChild] = field(default_factory=list)
    key: Optional[str] = None
    _el: Any = None  # Attached DOM element (client-side only)


def h(tag: str, props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create virtual DOM node.

    Args:
        tag: HTML tag name (e.g., "div", "span", "button")
        props: Optional dictionary of element properties and event handlers
        *children: Variable number of child VNodes or text strings

    Returns:
        VNode instance with specified tag, props, and children

    Examples:
        >>> h("div", {"class": "container"}, "Hello")
        VNode(tag='div', props={'class': 'container'}, children=['Hello'])

        >>> h("button", {"on_click": handler}, "Click me")
        VNode(tag='button', props={'on_click': <function>}, children=['Click me'])

    SEE: shared.vdom.VNode, shared.vdom.div, tests.unit.test-vdom.TestHFunction
    """
    return VNode(
        tag=tag,
        props=props or {},
        children=list(children)
    )


# ANCHOR: shared.vdom.helpers
# TITLE: HTML element helper functions
# ROLE: vdom/ergonomics layer
# SEE: shared.vdom.h, shared.vdom.VNode

def div(props: Optional[Dict[str, Any]] = None, *children: VNodeChild, **kwargs) -> VNode:
    """Create div element.

    Args:
        props: Optional element properties
        *children: Child VNodes or text strings
        **kwargs: Alternative way to pass children

    Returns:
        VNode with tag="div"

    SEE: shared.vdom.h
    """
    if 'children' in kwargs and not children:
        children = tuple(kwargs['children']) if isinstance(kwargs['children'], list) else (kwargs['children'],)
    return h("div", props, *children)


def button(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create button element. SEE: shared.vdom.h"""
    return h("button", props, *children)


def span(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create span element. SEE: shared.vdom.h"""
    return h("span", props, *children)


def h1(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create h1 heading element. SEE: shared.vdom.h"""
    return h("h1", props, *children)


def h2(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create h2 heading element. SEE: shared.vdom.h"""
    return h("h2", props, *children)


def h3(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create h3 heading element. SEE: shared.vdom.h"""
    return h("h3", props, *children)


def p(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create paragraph element. SEE: shared.vdom.h"""
    return h("p", props, *children)


def a(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create anchor (link) element. SEE: shared.vdom.h"""
    return h("a", props, *children)


def input_field(props: Optional[Dict[str, Any]] = None) -> VNode:
    """Create input element.

    Note: input is a self-closing tag with no children.

    SEE: shared.vdom.h
    """
    return h("input", props)


# Alias for input_field() - shorter name
input_ = input_field


def textarea(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create textarea element. SEE: shared.vdom.h"""
    return h("textarea", props, *children)


def select(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create select dropdown element. SEE: shared.vdom.h"""
    return h("select", props, *children)


def option(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create option element (for select). SEE: shared.vdom.h"""
    return h("option", props, *children)


def ul(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create unordered list element. SEE: shared.vdom.h"""
    return h("ul", props, *children)


def ol(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create ordered list element. SEE: shared.vdom.h"""
    return h("ol", props, *children)


def li(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create list item element. SEE: shared.vdom.h"""
    return h("li", props, *children)


def img(props: Optional[Dict[str, Any]] = None) -> VNode:
    """Create img element (self-closing). SEE: shared.vdom.h"""
    return h("img", props)


def br(props: Optional[Dict[str, Any]] = None) -> VNode:
    """Create br (line break) element (self-closing). SEE: shared.vdom.h"""
    return h("br", props)


def hr(props: Optional[Dict[str, Any]] = None) -> VNode:
    """Create hr (horizontal rule) element (self-closing). SEE: shared.vdom.h"""
    return h("hr", props)


def form(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create form element. SEE: shared.vdom.h"""
    return h("form", props, *children)


def label(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create label element. SEE: shared.vdom.h"""
    return h("label", props, *children)


def table(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create table element. SEE: shared.vdom.h"""
    return h("table", props, *children)


def tr(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create table row element. SEE: shared.vdom.h"""
    return h("tr", props, *children)


def td(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create table data cell element. SEE: shared.vdom.h"""
    return h("td", props, *children)


def th(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create table header cell element. SEE: shared.vdom.h"""
    return h("th", props, *children)


def nav(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create nav element. SEE: shared.vdom.h"""
    return h("nav", props, *children)


def header(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create header element. SEE: shared.vdom.h"""
    return h("header", props, *children)


def footer(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create footer element. SEE: shared.vdom.h"""
    return h("footer", props, *children)


def section(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create section element. SEE: shared.vdom.h"""
    return h("section", props, *children)


def article(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create article element. SEE: shared.vdom.h"""
    return h("article", props, *children)


def main(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create main element. SEE: shared.vdom.h"""
    return h("main", props, *children)


def aside(props: Optional[Dict[str, Any]] = None, *children: VNodeChild) -> VNode:
    """Create aside element. SEE: shared.vdom.h"""
    return h("aside", props, *children)

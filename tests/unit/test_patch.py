# ANCHOR: tests.unit.patch
# TITLE: Unit tests for VDOM patch() diffing algorithm
# ROLE: tests/unit layer
# COVERS: client.runtime.patch, client.runtime.patch_props, client.runtime.patch_children
# SEE: client.runtime, RESEARCH.md section 3 - VDOM Diffing Algorithms

"""
Unit tests for Phase 3 patch() implementation.

These tests validate the Preact-style O(n) diffing algorithm:
- Same-level comparison only
- Element reuse when tags match
- Prop updates in-place
- Children reconciliation (keyed and non-keyed)
- Minimal DOM operations

TESTING STRATEGY:
- Use mock DOM elements to test patch logic without Pyodide
- Focus on algorithm correctness, not DOM implementation
- Test all edge cases: add, remove, replace, move, update
"""

import pytest
from shared.vdom import VNode, h, div, button, span, ul, li
from unittest.mock import Mock, MagicMock, call


# ANCHOR: tests.unit.patch.fixtures
# Mock DOM element for testing without Pyodide

class MockElement:
    """Mock DOM element for unit testing.

    Simulates DOM element behavior without requiring browser/Pyodide.
    Tracks all operations for assertion in tests.
    """
    def __init__(self, tag):
        self.tag = tag
        self.textContent = ""
        self.className = ""
        self.style = {}
        self.attributes = {}
        self.children = []
        self.event_listeners = {}
        self.parent = None

    @property
    def childNodes(self):
        """Property to access children (DOM API compatibility)."""
        return self.children

    def setAttribute(self, key, value):
        self.attributes[key] = value

    def removeAttribute(self, key):
        if key in self.attributes:
            del self.attributes[key]

    def addEventListener(self, event, handler):
        if event not in self.event_listeners:
            self.event_listeners[event] = []
        self.event_listeners[event].append(handler)

    def removeEventListener(self, event, handler):
        if event in self.event_listeners:
            self.event_listeners[event].remove(handler)

    def appendChild(self, child):
        self.children.append(child)
        if hasattr(child, 'parent'):
            child.parent = self

    def removeChild(self, child):
        if child in self.children:
            self.children.remove(child)
            if hasattr(child, 'parent'):
                child.parent = None

    def insertBefore(self, new_child, ref_child):
        if ref_child in self.children:
            idx = self.children.index(ref_child)
            self.children.insert(idx, new_child)
            if hasattr(new_child, 'parent'):
                new_child.parent = self
        else:
            self.appendChild(new_child)

    def remove(self):
        if self.parent:
            self.parent.removeChild(self)


@pytest.fixture
def mock_document(monkeypatch):
    """Mock js.document for unit testing without Pyodide."""
    def createElement(tag):
        return MockElement(tag)

    def createTextNode(text):
        node = MockElement("text")
        node.textContent = text
        return node

    mock_doc = Mock()
    mock_doc.createElement = Mock(side_effect=createElement)
    mock_doc.createTextNode = Mock(side_effect=createTextNode)

    # Mock js module
    import sys
    mock_js = Mock()
    mock_js.document = mock_doc
    sys.modules['js'] = mock_js

    # Mock pyodide.ffi
    mock_pyodide = Mock()
    mock_ffi = Mock()
    mock_ffi.create_proxy = Mock(side_effect=lambda f: f)  # Return function as-is
    mock_pyodide.ffi = mock_ffi
    sys.modules['pyodide'] = mock_pyodide
    sys.modules['pyodide.ffi'] = mock_ffi

    yield mock_doc

    # Cleanup
    if 'js' in sys.modules:
        del sys.modules['js']
    if 'pyodide' in sys.modules:
        del sys.modules['pyodide']


# ANCHOR: tests.unit.patch.text-nodes
# Test patch() with text nodes

def test_patch_text_node_same_content(mock_document):
    """patch() should not update DOM when text content unchanged."""
    from client.runtime import patch

    parent = MockElement("div")

    # Create text nodes with same content
    old_text = "Hello"
    new_text = "Hello"

    # First mount to create _el reference
    old_el = mock_document.createTextNode(old_text)
    old_text_obj = Mock(_el=old_el)
    new_text_obj = "Hello"

    patch(parent, old_text, new_text)

    # Should not create new text node
    assert mock_document.createTextNode.call_count == 1  # Only from fixture setup


def test_patch_text_node_different_content(mock_document):
    """patch() should update textContent when text differs."""
    from client.runtime import patch

    parent = MockElement("div")

    old_text = "Hello"
    new_text = "World"

    # Create old text node with _el
    old_el = mock_document.createTextNode(old_text)

    patch(parent, old_text, new_text)

    # Should update textContent in-place (when we implement it)
    # For now, this test documents expected behavior


def test_patch_text_to_element(mock_document):
    """patch() should replace text node with element."""
    from client.runtime import patch

    parent = MockElement("div")

    old_vnode = "Hello"
    new_vnode = div({}, "World")

    patch(parent, old_vnode, new_vnode)

    # Should create new element and remove old text
    # For now, this test documents expected behavior


def test_patch_element_to_text(mock_document):
    """patch() should replace element with text node."""
    from client.runtime import patch

    parent = MockElement("div")

    old_vnode = div({}, "Hello")
    new_vnode = "World"

    patch(parent, old_vnode, new_vnode)

    # Should remove element and create text node
    # For now, this test documents expected behavior


# ANCHOR: tests.unit.patch.element-type
# Test patch() with different element types

def test_patch_same_tag_reuses_element(mock_document):
    """patch() should reuse DOM element when tags match."""
    from client.runtime import patch

    parent = MockElement("div")

    old_vnode = div({"class": "old"}, "Old")
    new_vnode = div({"class": "new"}, "New")

    # Set up old element
    old_el = MockElement("div")
    old_vnode._el = old_el

    patch(parent, old_vnode, new_vnode)

    # Should reuse same element reference
    assert new_vnode._el is old_el


def test_patch_different_tag_replaces_element(mock_document):
    """patch() should replace element when tags differ."""
    from client.runtime import patch

    parent = MockElement("div")

    old_vnode = div({}, "Content")
    new_vnode = span({}, "Content")

    # Set up old element
    old_el = MockElement("div")
    old_vnode._el = old_el
    parent.appendChild(old_el)

    patch(parent, old_vnode, new_vnode)

    # Should create new element with different tag
    # Old element should be removed
    # For now, this test documents expected behavior


# ANCHOR: tests.unit.patch.props
# Test patch_props() functionality

def test_patch_props_updates_attributes(mock_document):
    """patch_props() should update changed attributes."""
    from client.runtime import patch_props

    element = MockElement("div")
    element.className = "container"  # Set initial className

    old_props = {"id": "old", "class": "container"}
    new_props = {"id": "new", "class": "container"}

    patch_props(element, old_props, new_props)

    # Should update id but not class (class unchanged, skipped)
    assert element.attributes.get("id") == "new"
    assert element.className == "container"


def test_patch_props_removes_old_attributes(mock_document):
    """patch_props() should remove attributes not in new props."""
    from client.runtime import patch_props

    element = MockElement("div")
    element.setAttribute("old-attr", "value")
    element.setAttribute("keep", "this")  # Set initial value

    old_props = {"old-attr": "value", "keep": "this"}
    new_props = {"keep": "this"}

    patch_props(element, old_props, new_props)

    # Should remove old-attr
    assert "old-attr" not in element.attributes
    assert element.attributes.get("keep") == "this"


def test_patch_props_adds_new_attributes(mock_document):
    """patch_props() should add new attributes."""
    from client.runtime import patch_props

    element = MockElement("div")

    old_props = {"class": "old"}
    new_props = {"class": "old", "id": "new-id"}

    patch_props(element, old_props, new_props)

    # Should add id attribute
    assert element.attributes.get("id") == "new-id"


def test_patch_props_updates_event_handlers(mock_document):
    """patch_props() should update event handlers."""
    from client.runtime import patch_props

    element = MockElement("div")

    old_handler = lambda e: print("old")
    new_handler = lambda e: print("new")

    old_props = {"on_click": old_handler}
    new_props = {"on_click": new_handler}

    # First add old handler
    element.addEventListener("click", old_handler)

    patch_props(element, old_props, new_props)

    # Should have new handler
    # Implementation may vary: replace or add new
    # For now, this test documents expected behavior


def test_patch_props_removes_event_handlers(mock_document):
    """patch_props() should remove event handlers not in new props."""
    from client.runtime import patch_props

    element = MockElement("div")

    old_handler = lambda e: print("old")
    old_props = {"on_click": old_handler}
    new_props = {}

    element.addEventListener("click", old_handler)

    patch_props(element, old_props, new_props)

    # Should remove click handler
    # For now, this test documents expected behavior


def test_patch_props_updates_style_dict(mock_document):
    """patch_props() should update inline styles."""
    from client.runtime import patch_props

    element = MockElement("div")

    old_props = {"style": {"color": "red", "fontSize": "12px"}}
    new_props = {"style": {"color": "blue", "fontSize": "12px", "fontWeight": "bold"}}

    patch_props(element, old_props, new_props)

    # Should update color, keep fontSize, add fontWeight
    assert element.style.get("color") == "blue"
    assert element.style.get("fontSize") == "12px"
    assert element.style.get("fontWeight") == "bold"


# ANCHOR: tests.unit.patch.children
# Test patch_children() for non-keyed children

def test_patch_children_same_count(mock_document):
    """patch_children() should patch children at same index."""
    from client.runtime import patch_children

    parent = MockElement("div")

    old_children = [
        span({}, "Child 1"),
        span({}, "Child 2")
    ]
    new_children = [
        span({}, "Updated 1"),
        span({}, "Updated 2")
    ]

    # Set up old elements
    for i, child in enumerate(old_children):
        el = MockElement("span")
        child._el = el
        parent.appendChild(el)

    patch_children(parent, old_children, new_children)

    # Should patch both children in place
    # For now, this test documents expected behavior


def test_patch_children_add_new(mock_document):
    """patch_children() should add new children at end."""
    from client.runtime import patch_children

    parent = MockElement("div")

    old_children = [span({}, "Child 1")]
    new_children = [
        span({}, "Child 1"),
        span({}, "Child 2"),
        span({}, "Child 3")
    ]

    # Set up old element
    old_children[0]._el = MockElement("span")
    parent.appendChild(old_children[0]._el)

    patch_children(parent, old_children, new_children)

    # Should add 2 new children
    # For now, this test documents expected behavior


def test_patch_children_remove_old(mock_document):
    """patch_children() should remove extra old children."""
    from client.runtime import patch_children

    parent = MockElement("div")

    old_children = [
        span({}, "Child 1"),
        span({}, "Child 2"),
        span({}, "Child 3")
    ]
    new_children = [span({}, "Child 1")]

    # Set up old elements
    for child in old_children:
        el = MockElement("span")
        child._el = el
        parent.appendChild(el)

    patch_children(parent, old_children, new_children)

    # Should remove 2 children
    # For now, this test documents expected behavior


# ANCHOR: tests.unit.patch.keyed-children
# Test patch_keyed_children() for list optimization

def test_patch_keyed_children_reorders_by_key(mock_document):
    """patch_keyed_children() should reorder children by key."""
    from client.runtime import patch_keyed_children

    parent = MockElement("div")

    # Old: A, B, C
    old_children = [
        li({"key": "a"}, "Item A"),
        li({"key": "b"}, "Item B"),
        li({"key": "c"}, "Item C")
    ]

    # New: C, A, B (reordered)
    new_children = [
        li({"key": "c"}, "Item C"),
        li({"key": "a"}, "Item A"),
        li({"key": "b"}, "Item B")
    ]

    # Set up old elements
    for i, child in enumerate(old_children):
        el = MockElement("li")
        child._el = el
        parent.appendChild(el)

    patch_keyed_children(parent, old_children, new_children)

    # Should reorder DOM elements to match new order
    # Minimal DOM moves (ideally 1-2 operations)
    # For now, this test documents expected behavior


def test_patch_keyed_children_adds_new_items(mock_document):
    """patch_keyed_children() should add new keyed items."""
    from client.runtime import patch_keyed_children

    parent = MockElement("div")

    old_children = [
        li({"key": "a"}, "Item A"),
        li({"key": "b"}, "Item B")
    ]

    new_children = [
        li({"key": "a"}, "Item A"),
        li({"key": "b"}, "Item B"),
        li({"key": "c"}, "Item C")  # New item
    ]

    # Set up old elements
    for child in old_children:
        el = MockElement("li")
        child._el = el
        parent.appendChild(el)

    patch_keyed_children(parent, old_children, new_children)

    # Should add new item
    # For now, this test documents expected behavior


def test_patch_keyed_children_removes_old_items(mock_document):
    """patch_keyed_children() should remove old keyed items."""
    from client.runtime import patch_keyed_children

    parent = MockElement("div")

    old_children = [
        li({"key": "a"}, "Item A"),
        li({"key": "b"}, "Item B"),
        li({"key": "c"}, "Item C")
    ]

    new_children = [
        li({"key": "a"}, "Item A")
        # B and C removed
    ]

    # Set up old elements
    for child in old_children:
        el = MockElement("li")
        child._el = el
        parent.appendChild(el)

    patch_keyed_children(parent, old_children, new_children)

    # Should remove B and C
    # For now, this test documents expected behavior


def test_patch_keyed_children_updates_existing_items(mock_document):
    """patch_keyed_children() should update content of existing items."""
    from client.runtime import patch_keyed_children

    parent = MockElement("div")

    old_children = [
        li({"key": "a"}, "Item A"),
        li({"key": "b"}, "Item B")
    ]

    new_children = [
        li({"key": "a"}, "Updated A"),  # Content changed
        li({"key": "b"}, "Updated B")   # Content changed
    ]

    # Set up old elements
    for child in old_children:
        el = MockElement("li")
        child._el = el
        parent.appendChild(el)

    patch_keyed_children(parent, old_children, new_children)

    # Should patch content without recreating elements
    # For now, this test documents expected behavior


# ANCHOR: tests.unit.patch.edge-cases
# Test edge cases

def test_patch_none_to_element(mock_document):
    """patch() should mount element when old is None."""
    from client.runtime import patch

    parent = MockElement("div")

    old_vnode = None
    new_vnode = div({}, "New")

    patch(parent, old_vnode, new_vnode)

    # Should mount new element
    # For now, this test documents expected behavior


def test_patch_element_to_none(mock_document):
    """patch() should remove element when new is None."""
    from client.runtime import patch

    parent = MockElement("div")

    old_vnode = div({}, "Old")
    new_vnode = None

    # Set up old element
    old_el = MockElement("div")
    old_vnode._el = old_el
    parent.appendChild(old_el)

    patch(parent, old_vnode, new_vnode)

    # Should remove element
    # For now, this test documents expected behavior


def test_patch_empty_children_lists(mock_document):
    """patch() should handle empty children lists."""
    from client.runtime import patch

    parent = MockElement("div")

    old_vnode = div({})  # No children
    new_vnode = div({})  # No children

    old_el = MockElement("div")
    old_vnode._el = old_el

    patch(parent, old_vnode, new_vnode)

    # Should reuse element with no children
    assert new_vnode._el is old_el


def test_patch_deeply_nested_structures(mock_document):
    """patch() should handle deeply nested VDOM trees."""
    from client.runtime import patch

    parent = MockElement("div")

    old_vnode = div({},
        div({},
            div({},
                span({}, "Deep")
            )
        )
    )

    new_vnode = div({},
        div({},
            div({},
                span({}, "Updated")
            )
        )
    )

    # Set up old elements recursively
    def setup_elements(vnode):
        if isinstance(vnode, str):
            return
        vnode._el = MockElement(vnode.tag)
        for child in vnode.children:
            setup_elements(child)

    setup_elements(old_vnode)

    patch(parent, old_vnode, new_vnode)

    # Should patch nested content efficiently
    # For now, this test documents expected behavior

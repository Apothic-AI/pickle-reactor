# ANCHOR: tests.unit.vdom
# TITLE: Unit tests for VDOM implementation
# COVERS: shared.vdom.VNode, shared.vdom.h, shared.vdom.helpers
# ROLE: testing/unit layer
# SCENARIOS: VNode creation, prop handling, children nesting, key assignment, HTML helpers

"""
Unit tests for Virtual DOM (VDOM) implementation.

Tests cover:
- VNode dataclass creation and structure
- h() helper function
- HTML element helpers (div, button, span, etc.)
- Props handling including event handlers
- Children nesting and text nodes
- Key assignment for list reconciliation
"""

import pytest
from shared.vdom import VNode, h, div, button, span, h1, p, input_field


class TestVNodeCreation:
    """Test VNode dataclass creation and basic structure."""

    def test_vnode_with_tag_only(self):
        """VNode can be created with just a tag name."""
        node = VNode(tag="div")
        assert node.tag == "div"
        assert node.props == {}
        assert node.children == []
        assert node.key is None

    def test_vnode_with_props(self):
        """VNode stores props correctly."""
        props = {"class": "container", "id": "main"}
        node = VNode(tag="div", props=props)
        assert node.tag == "div"
        assert node.props == props
        assert node.props["class"] == "container"
        assert node.props["id"] == "main"

    def test_vnode_with_children(self):
        """VNode stores children as list."""
        children = ["Hello", "World"]
        node = VNode(tag="div", children=children)
        assert len(node.children) == 2
        assert node.children[0] == "Hello"
        assert node.children[1] == "World"

    def test_vnode_with_key(self):
        """VNode can have a key for list reconciliation."""
        node = VNode(tag="li", key="item-1")
        assert node.key == "item-1"


class TestHFunction:
    """Test h() helper function for creating VNodes."""

    def test_h_creates_vnode(self):
        """h() creates a VNode with correct tag."""
        node = h("div")
        assert isinstance(node, VNode)
        assert node.tag == "div"

    def test_h_with_props(self):
        """h() handles props parameter."""
        node = h("div", {"class": "box"})
        assert node.props["class"] == "box"

    def test_h_with_single_child(self):
        """h() handles single text child."""
        node = h("div", {}, "Hello")
        assert len(node.children) == 1
        assert node.children[0] == "Hello"

    def test_h_with_multiple_children(self):
        """h() handles multiple children via *args."""
        node = h("div", {}, "Hello", " ", "World")
        assert len(node.children) == 3
        assert node.children == ["Hello", " ", "World"]

    def test_h_with_nested_vnodes(self):
        """h() handles nested VNode children."""
        inner = h("span", {}, "inner")
        outer = h("div", {}, inner, "text")
        assert len(outer.children) == 2
        assert outer.children[0] == inner
        assert outer.children[1] == "text"

    def test_h_with_none_props(self):
        """h() handles None props gracefully."""
        node = h("div", None, "content")
        assert node.props == {}
        assert node.children[0] == "content"


class TestEventHandlerProps:
    """Test event handler props (on_* pattern)."""

    def test_event_handler_in_props(self):
        """VNode accepts callable event handlers in props."""
        def handler(e):
            return "clicked"

        node = h("button", {"on_click": handler}, "Click me")
        assert callable(node.props["on_click"])
        assert node.props["on_click"](None) == "clicked"

    def test_multiple_event_handlers(self):
        """VNode can have multiple event handlers."""
        def click_handler(e):
            pass

        def input_handler(e):
            pass

        node = h("input", {
            "on_click": click_handler,
            "on_input": input_handler
        })
        assert callable(node.props["on_click"])
        assert callable(node.props["on_input"])


class TestHTMLHelpers:
    """Test HTML element helper functions."""

    def test_div_helper(self):
        """div() creates div VNode."""
        node = div({}, "content")
        assert node.tag == "div"
        assert node.children[0] == "content"

    def test_button_helper(self):
        """button() creates button VNode."""
        node = button({}, "Click")
        assert node.tag == "button"
        assert node.children[0] == "Click"

    def test_span_helper(self):
        """span() creates span VNode."""
        node = span({}, "text")
        assert node.tag == "span"

    def test_h1_helper(self):
        """h1() creates h1 VNode."""
        node = h1({}, "Title")
        assert node.tag == "h1"

    def test_p_helper(self):
        """p() creates p VNode."""
        node = p({}, "Paragraph")
        assert node.tag == "p"

    def test_input_helper(self):
        """input_field() creates input VNode."""
        node = input_field({"type": "text"})
        assert node.tag == "input"
        assert node.props["type"] == "text"

    def test_helper_with_no_props(self):
        """Helpers work without props argument."""
        node = div(children=["content"])
        assert node.tag == "div"
        assert node.children[0] == "content"


class TestNestedStructures:
    """Test complex nested VDOM structures."""

    def test_deeply_nested_vnodes(self):
        """VNodes can be deeply nested."""
        innermost = span({}, "text")
        middle = p({}, innermost)
        outer = div({}, middle)

        assert outer.tag == "div"
        assert outer.children[0].tag == "p"
        assert outer.children[0].children[0].tag == "span"
        assert outer.children[0].children[0].children[0] == "text"

    def test_mixed_children_types(self):
        """VNode children can be mix of strings and VNodes."""
        child_vnode = span({}, "highlighted")
        parent = div({}, "Before ", child_vnode, " after")

        assert len(parent.children) == 3
        assert parent.children[0] == "Before "
        assert isinstance(parent.children[1], VNode)
        assert parent.children[2] == " after"

    def test_list_of_children(self):
        """VNode can contain list of similar children (for mapping)."""
        items = [
            div({"key": "1"}, "Item 1"),
            div({"key": "2"}, "Item 2"),
            div({"key": "3"}, "Item 3")
        ]
        container = div({}, *items)

        assert len(container.children) == 3
        assert all(isinstance(child, VNode) for child in container.children)


class TestKeyBasedReconciliation:
    """Test key prop for list reconciliation."""

    def test_vnode_key_assignment(self):
        """VNode key can be assigned for reconciliation."""
        node = VNode(tag="li", key="item-123")
        assert node.key == "item-123"

    def test_keys_in_list_items(self):
        """List items should have unique keys."""
        items = [
            div({"key": f"item-{i}"}, f"Item {i}")
            for i in range(3)
        ]

        assert items[0].props["key"] == "item-0"
        assert items[1].props["key"] == "item-1"
        assert items[2].props["key"] == "item-2"


class TestPropsHandling:
    """Test various props handling scenarios."""

    def test_boolean_props(self):
        """Boolean props are stored correctly."""
        node = h("button", {"disabled": True}, "Submit")
        assert node.props["disabled"] is True

    def test_style_dict_prop(self):
        """Style can be passed as dictionary."""
        node = div({"style": {"color": "red", "fontSize": "16px"}})
        assert isinstance(node.props["style"], dict)
        assert node.props["style"]["color"] == "red"

    def test_data_attributes(self):
        """Data attributes are stored in props."""
        node = div({"data-id": "123", "data-type": "container"})
        assert node.props["data-id"] == "123"
        assert node.props["data-type"] == "container"

    def test_empty_props(self):
        """VNode with empty props dict works correctly."""
        node = h("div", {})
        assert node.props == {}

    def test_none_prop_values(self):
        """None prop values are stored correctly."""
        node = h("input", {"value": None})
        assert node.props["value"] is None


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_children_list(self):
        """VNode with empty children list."""
        node = h("div", {})
        assert node.children == []

    def test_single_empty_string_child(self):
        """VNode with empty string child."""
        node = h("div", {}, "")
        assert len(node.children) == 1
        assert node.children[0] == ""

    def test_numeric_children(self):
        """VNode can have numeric string children."""
        node = h("span", {}, "42")
        assert node.children[0] == "42"

    def test_special_characters_in_text(self):
        """VNode can contain text with special characters."""
        node = h("p", {}, "<script>alert('xss')</script>")
        assert node.children[0] == "<script>alert('xss')</script>"
        # Note: Escaping happens in render phase, not in VNode creation

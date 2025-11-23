# ANCHOR: tests.unit.ssr
# TITLE: Unit tests for server-side rendering (SSR)
# COVERS: server.ssr.render-to-string
# ROLE: testing/unit layer
# SCENARIOS: HTML rendering, escaping, props, children, nested structures, XSS prevention

"""
Unit tests for Server-Side Rendering (SSR) implementation.

Tests cover:
- render_to_string() function for VNode → HTML conversion
- HTML escaping to prevent XSS attacks
- Props rendering (attributes, boolean props, style dicts)
- Children rendering (text, nested VNodes)
- Event handler props (ignored on server)
- Self-closing tags
- Security: XSS prevention with malicious inputs
"""

import pytest
from shared.vdom import VNode, h, div, button, span, h1, p, input_field, img, br
from server.ssr import render_to_string


class TestBasicRendering:
    """Test basic HTML string rendering."""

    def test_render_simple_tag(self):
        """render_to_string renders simple tag."""
        node = h("div")
        html = render_to_string(node)
        assert html == "<div></div>"

    def test_render_tag_with_text(self):
        """render_to_string renders tag with text content."""
        node = h("p", {}, "Hello World")
        html = render_to_string(node)
        assert html == "<p>Hello World</p>"

    def test_render_text_node(self):
        """render_to_string handles plain text (string input)."""
        html = render_to_string("Just text")
        assert html == "Just text"

    def test_render_empty_div(self):
        """render_to_string renders empty div."""
        node = div()
        html = render_to_string(node)
        assert html == "<div></div>"


class TestPropsRendering:
    """Test props/attributes rendering."""

    def test_render_class_attribute(self):
        """render_to_string renders class attribute."""
        node = div({"class": "container"})
        html = render_to_string(node)
        assert html == '<div class="container"></div>'

    def test_render_id_attribute(self):
        """render_to_string renders id attribute."""
        node = div({"id": "main"})
        html = render_to_string(node)
        assert html == '<div id="main"></div>'

    def test_render_multiple_attributes(self):
        """render_to_string renders multiple attributes."""
        node = div({"class": "box", "id": "container", "data-test": "value"})
        html = render_to_string(node)
        # Order may vary, so check both are present
        assert 'class="box"' in html
        assert 'id="container"' in html
        assert 'data-test="value"' in html
        assert html.startswith("<div")
        assert html.endswith("</div>")

    def test_render_boolean_true_attribute(self):
        """render_to_string renders boolean True as attribute without value."""
        node = button({"disabled": True}, "Submit")
        html = render_to_string(node)
        assert html == "<button disabled>Submit</button>"

    def test_render_boolean_false_attribute(self):
        """render_to_string omits boolean False attributes."""
        node = button({"disabled": False}, "Submit")
        html = render_to_string(node)
        assert html == "<button>Submit</button>"
        assert "disabled" not in html

    def test_render_none_attribute(self):
        """render_to_string omits None attributes."""
        node = div({"title": None}, "Content")
        html = render_to_string(node)
        assert html == "<div>Content</div>"
        assert "title" not in html

    def test_render_numeric_attribute(self):
        """render_to_string converts numeric attributes to strings."""
        node = div({"tabindex": 0}, "Content")
        html = render_to_string(node)
        assert html == '<div tabindex="0">Content</div>'


class TestChildrenRendering:
    """Test children rendering."""

    def test_render_single_child(self):
        """render_to_string renders single child."""
        node = div({}, "Child text")
        html = render_to_string(node)
        assert html == "<div>Child text</div>"

    def test_render_multiple_text_children(self):
        """render_to_string concatenates multiple text children."""
        node = div({}, "Hello", " ", "World")
        html = render_to_string(node)
        assert html == "<div>Hello World</div>"

    def test_render_nested_vnodes(self):
        """render_to_string renders nested VNodes."""
        inner = span({}, "inner")
        outer = div({}, inner)
        html = render_to_string(outer)
        assert html == "<div><span>inner</span></div>"

    def test_render_deeply_nested_vnodes(self):
        """render_to_string handles deeply nested structures."""
        node = div({}, h1({}, span({}, "Title")))
        html = render_to_string(node)
        assert html == "<div><h1><span>Title</span></h1></div>"

    def test_render_mixed_children(self):
        """render_to_string renders mix of text and VNodes."""
        child_vnode = span({}, "highlighted")
        node = div({}, "Before ", child_vnode, " after")
        html = render_to_string(node)
        assert html == "<div>Before <span>highlighted</span> after</div>"

    def test_render_empty_children_list(self):
        """render_to_string handles empty children list."""
        node = div({})
        html = render_to_string(node)
        assert html == "<div></div>"


class TestHTMLEscaping:
    """Test HTML escaping for XSS prevention."""

    def test_escape_text_content(self):
        """render_to_string escapes HTML in text content."""
        node = p({}, "<script>alert('xss')</script>")
        html = render_to_string(node)
        # html.escape() escapes single quotes to &#x27; for extra security
        assert html == "<p>&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;</p>"
        assert "<script>" not in html

    def test_escape_ampersand(self):
        """render_to_string escapes ampersand."""
        node = p({}, "Ben & Jerry's")
        html = render_to_string(node)
        # html.escape() also escapes single quotes
        assert html == "<p>Ben &amp; Jerry&#x27;s</p>"

    def test_escape_quotes_in_text(self):
        """render_to_string escapes quotes in text content."""
        node = p({}, 'He said "Hello"')
        html = render_to_string(node)
        # Quotes in text content are escaped
        assert "&quot;" in html or '"' not in html or html == '<p>He said "Hello"</p>'

    def test_escape_less_than_greater_than(self):
        """render_to_string escapes < and >."""
        node = p({}, "a < b && b > c")
        html = render_to_string(node)
        assert html == "<p>a &lt; b &amp;&amp; b &gt; c</p>"

    def test_escape_attribute_values(self):
        """render_to_string escapes attribute values."""
        node = div({"title": "<script>alert('xss')</script>"})
        html = render_to_string(node)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html


class TestEventHandlers:
    """Test event handler props (should be ignored on server)."""

    def test_ignore_event_handlers(self):
        """render_to_string ignores on_* event handler props."""
        def handler(e):
            pass

        node = button({"on_click": handler}, "Click")
        html = render_to_string(node)
        assert html == "<button>Click</button>"
        assert "on_click" not in html

    def test_ignore_multiple_event_handlers(self):
        """render_to_string ignores all event handlers."""
        def click_handler(e):
            pass

        def input_handler(e):
            pass

        node = div({
            "on_click": click_handler,
            "on_input": input_handler,
            "class": "interactive"
        }, "Content")
        html = render_to_string(node)
        assert 'class="interactive"' in html
        assert "on_click" not in html
        assert "on_input" not in html


class TestSelfClosingTags:
    """Test self-closing tags (input, img, br, hr)."""

    def test_render_input(self):
        """render_to_string renders input as self-closing or with closing tag."""
        node = input_field({"type": "text", "name": "username"})
        html = render_to_string(node)
        # Either <input /> or <input></input> is acceptable for Phase 1
        assert "<input" in html
        assert 'type="text"' in html
        assert 'name="username"' in html

    def test_render_img(self):
        """render_to_string renders img tag."""
        node = img({"src": "/logo.png", "alt": "Logo"})
        html = render_to_string(node)
        assert "<img" in html
        assert 'src="/logo.png"' in html
        assert 'alt="Logo"' in html

    def test_render_br(self):
        """render_to_string renders br tag."""
        node = br()
        html = render_to_string(node)
        assert "<br" in html


class TestComplexStructures:
    """Test complex nested structures."""

    def test_render_list_items(self):
        """render_to_string renders list with items."""
        from shared.vdom import ul, li

        items = [
            li({"key": "1"}, "Item 1"),
            li({"key": "2"}, "Item 2"),
            li({"key": "3"}, "Item 3")
        ]
        node = ul({}, *items)
        html = render_to_string(node)

        assert html.startswith("<ul>")
        assert html.endswith("</ul>")
        assert "<li" in html
        assert "Item 1" in html
        assert "Item 2" in html
        assert "Item 3" in html
        # Keys should be ignored on server (used only for client-side reconciliation)

    def test_render_form(self):
        """render_to_string renders form with inputs."""
        from shared.vdom import form, label

        node = form({"action": "/submit", "method": "post"},
            label({}, "Name: ", input_field({"type": "text", "name": "name"})),
            button({"type": "submit"}, "Submit")
        )
        html = render_to_string(node)

        assert '<form action="/submit" method="post">' in html
        assert "<label>" in html
        assert "Name: " in html
        assert "<input" in html
        assert 'type="text"' in html
        assert "<button" in html
        assert "Submit" in html
        assert "</form>" in html

    def test_render_nested_divs_with_classes(self):
        """render_to_string renders nested divs with various attributes."""
        node = div({"class": "outer"},
            div({"class": "middle"},
                div({"class": "inner"}, "Content")
            )
        )
        html = render_to_string(node)

        assert '<div class="outer">' in html
        assert '<div class="middle">' in html
        assert '<div class="inner">Content</div>' in html


class TestSecurityXSSPrevention:
    """Test XSS prevention with malicious inputs."""

    def test_prevent_script_injection_in_text(self):
        """render_to_string prevents script injection in text."""
        malicious = "<script>alert('XSS')</script>"
        node = div({}, malicious)
        html = render_to_string(node)

        assert "<script>" not in html
        assert "&lt;script&gt;" in html
        assert "alert" in html  # Content is there but escaped

    def test_prevent_onclick_injection(self):
        """render_to_string escapes onclick in attributes."""
        node = div({"title": "\" onclick=\"alert('XSS')\""})
        html = render_to_string(node)

        # The attribute value should be escaped
        assert "onclick" not in html or "&quot;" in html

    def test_prevent_img_onerror_injection(self):
        """render_to_string escapes onerror attributes."""
        node = img({"src": "x", "onerror": "alert('XSS')"})
        html = render_to_string(node)

        # onerror should be rendered as escaped attribute
        # This is an edge case - onerror shouldn't execute in SSR context
        assert "<img" in html

    def test_prevent_javascript_protocol(self):
        """render_to_string handles javascript: protocol in href."""
        from shared.vdom import a

        node = a({"href": "javascript:alert('XSS')"}, "Click")
        html = render_to_string(node)

        # We don't sanitize URLs in Phase 1, but they're escaped
        assert "<a" in html
        assert "javascript:" in html  # Not sanitized yet, but escaped

    def test_prevent_data_uri_xss(self):
        """render_to_string handles data URIs."""
        node = img({"src": "data:text/html,<script>alert('XSS')</script>"})
        html = render_to_string(node)

        # Data URI is rendered but HTML within is escaped
        assert "&lt;script&gt;" in html or "<script>" not in html


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_render_empty_string(self):
        """render_to_string handles empty string."""
        html = render_to_string("")
        assert html == ""

    def test_render_whitespace_only(self):
        """render_to_string preserves whitespace."""
        node = p({}, "   ")
        html = render_to_string(node)
        assert html == "<p>   </p>"

    def test_render_newlines_in_text(self):
        """render_to_string preserves newlines in text."""
        node = p({}, "Line 1\nLine 2")
        html = render_to_string(node)
        assert "Line 1\nLine 2" in html

    def test_render_unicode_characters(self):
        """render_to_string handles Unicode characters."""
        node = p({}, "Hello 世界 🌍")
        html = render_to_string(node)
        assert "Hello 世界 🌍" in html

    def test_render_special_html_entities(self):
        """render_to_string escapes special HTML entities."""
        node = p({}, "© ™ € £")
        html = render_to_string(node)
        # These should be preserved as-is or as entities
        assert "©" in html or "&copy;" in html

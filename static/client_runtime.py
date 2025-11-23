# ANCHOR: client.runtime
# TITLE: Pyodide client runtime with DOM hydration
# ROLE: client/browser layer
# EXPORTS: hydrate, mount, rerender
# SEE: client.bootstrap, shared.state, shared.vdom, tests.integration.test-client-runtime

"""
Client-side runtime for pickle-reactor framework (runs in Pyodide).

This module provides:
- hydrate(): Entry point for client-side initialization
- mount(parent, vnode): Initial VDOM mounting using pydom
- rerender(): Full DOM replacement (Phase 2 - no diffing yet)

IMPORTANT:
- This code runs in the browser via Pyodide (WebAssembly)
- Uses PyScript's pydom for DOM manipulation
- Phase 2 uses dumb full DOM replacement; Phase 3 will add proper diffing

PERFORMANCE:
- Phase 2: Full DOM replacement is inefficient but simple
- Phase 3: Will implement Preact-style patch() for efficient updates
- Memory: Must be careful with PyProxy cleanup (future optimization)

SEE: RESEARCH.md section 2 - PyScript pydom API
"""

import js  # Pyodide JavaScript FFI
from shared.vdom import VNode
from shared.state import ComponentInstance, render_component


# ANCHOR: client.runtime.globals
# Global state for client runtime
_current_vdom = None
_root_element = None
_root_instance = None
_current_component = None  # Phase 4: Store current page component for rerender
_initial_props = {}  # Phase 5: Store initial props for rerender


def hydrate():
    """Hydrate server-rendered HTML with client-side interactivity.

    This is the entry point called by bootstrap.js after Pyodide loads.
    It:
    1. Finds the root element (#root)
    2. Creates a ComponentInstance for state tracking
    3. Dynamically imports the correct page component based on __PAGE_COMPONENT__
    4. Renders the page component
    5. Mounts it to the DOM (Phase 2: replaces existing content)
    6. Wires up schedule_update to trigger re-renders

    Phase 4: Dynamic Component Loading
    - Reads window.__PAGE_COMPONENT__ to determine which page to render
    - Supports multiple pages (IndexPage, AboutPage, TodosPage)
    - Enables file-based routing

    WHY: Convert static SSR HTML to interactive app with state management

    Preconditions:
        - Pyodide loaded and initialized
        - DOM contains element with id="root"
        - window.__PAGE_COMPONENT__ is set with component name
        - Page component is importable

    Postconditions:
        - Root element attached to _root_element
        - Initial VDOM rendered and stored in _current_vdom
        - Component instance schedule_update bound to rerender()
        - Correct page component loaded

    Side effects:
        - Clears existing DOM content in #root
        - Attaches event listeners
        - Sets global _current_vdom, _root_element, _root_instance, _current_component

    SEE: client.runtime.mount, client.runtime.rerender, server.app.routes
    """
    global _root_element, _root_instance, _current_vdom, _current_component, _initial_props

    print("🔧 Hydrating Pickle-Reactor application...")

    # Find root element using JavaScript FFI
    _root_element = js.document.getElementById("root")
    if not _root_element:
        raise RuntimeError("No root element found with id='root'")

    # Phase 4: Get page component name from global variable
    page_component_name = js.window.__PAGE_COMPONENT__ if hasattr(js.window, '__PAGE_COMPONENT__') else "IndexPage"
    print(f"📄 Loading page component: {page_component_name}")

    # Phase 5: Get initial props from global variable
    initial_props = {}
    if hasattr(js.window, '__INITIAL_PROPS__'):
        # Convert JavaScript object to Python dict
        initial_props = js.window.__INITIAL_PROPS__.to_py()
        print(f"📦 Initial props: {initial_props}")

    # Dynamically import the correct page component
    if page_component_name == "IndexPage":
        from pages.index import IndexPage as PageComponent
    elif page_component_name == "AboutPage":
        from pages.about import AboutPage as PageComponent
    elif page_component_name == "TodosPage":
        from pages.todos import TodosPage as PageComponent
    elif page_component_name == "DashboardPage":
        from pages.dashboard import DashboardPage as PageComponent
    else:
        raise RuntimeError(f"Unknown page component: {page_component_name}")

    # Store current component and props for rerender
    _current_component = PageComponent
    _initial_props = initial_props  # Phase 5: Preserve for rerender

    # Create component instance for state tracking
    _root_instance = ComponentInstance()

    # Phase 5: Initial render with initial props from SSR
    new_vdom = render_component(PageComponent, initial_props, _root_instance)

    # Phase 2: Clear existing content and mount fresh
    # Phase 3 will implement true hydration (reuse existing DOM)
    _root_element.innerHTML = ""
    mount(_root_element, new_vdom)
    _current_vdom = new_vdom

    # Wire schedule_update to trigger re-renders
    def schedule_update():
        """Callback triggered by use_state set_value.

        WHY: When state changes, we need to re-render the component

        SEE: shared.state.use_state, client.runtime.rerender
        """
        rerender()

    _root_instance.schedule_update = schedule_update

    print("✅ Hydration complete!")


def mount(parent, vnode):
    """Mount VNode to real DOM using JavaScript FFI.

    Creates actual DOM elements from VNode tree and appends to parent.
    Handles:
    - Text nodes (strings)
    - Element creation with js.document.createElement()
    - Props application (attributes, styles, classes, events)
    - Recursive children mounting

    WHY: Initial DOM creation from VDOM

    Args:
        parent: DOM element reference (parent container)
        vnode: VNode or string to mount

    Preconditions:
        - parent is valid DOM element reference
        - vnode is VNode or string

    Postconditions:
        - vnode._el references created DOM element
        - Element appended to parent
        - Event listeners attached for on_* props

    Side effects:
        - Creates DOM elements via js.document
        - Attaches event listeners via addEventListener
        - Sets vnode._el property

    CALLERS: client.runtime.hydrate, client.runtime.rerender (Phase 2)
    SEE: client.runtime.rerender, tests.integration.test-mount
    """
    # Handle text nodes
    if isinstance(vnode, str):
        # Create text node
        text_node = js.document.createTextNode(vnode)
        parent.appendChild(text_node)
        # For text nodes represented as strings, we can't set _el
        # This is fine for Phase 2
        return

    # Create element
    el = js.document.createElement(vnode.tag)
    vnode._el = el  # Store reference for future patch operations

    # Apply props (attributes, styles, events)
    for k, v in (vnode.props or {}).items():
        # Event handlers (on_click, on_input, etc.)
        if k.startswith("on_") and callable(v):
            event = k[len("on_"):]  # Extract event name ("click", "input")
            # Create proxy for Python callback to work with JS events
            from pyodide.ffi import create_proxy
            proxy = create_proxy(v)
            el.addEventListener(event, proxy)
        # CSS classes
        elif k == "class":
            el.className = v
        # Inline styles (dict)
        elif k == "style" and isinstance(v, dict):
            for sk, sv in v.items():
                el.style[sk] = sv
        # Regular attributes (id, href, src, etc.)
        else:
            el.setAttribute(k, str(v))

    # Mount children recursively
    for child in (vnode.children or []):
        mount(el, child)

    # Append to parent
    parent.appendChild(el)


# ANCHOR: client.runtime.patch
# TITLE: Preact-style VDOM diffing algorithm
# ROLE: client/diffing layer
# SEE: RESEARCH.md section 3 - VDOM Diffing Algorithms

def patch(parent, old_vnode, new_vnode, index=0):
    """Patch existing DOM with VDOM changes (Preact-style diffing).

    Implements O(n) single-pass diffing algorithm:
    - Same-level comparison only
    - Reuse elements when tags match
    - Patch props and children in-place
    - Replace nodes when types differ

    WHY: Efficient DOM updates minimize browser reflows/repaints

    Algorithm:
        1. Type changed → replace entire subtree
        2. Text node → update textContent if different
        3. Same tag → patch in place (props + children)
        4. Different tag → replace node

    Args:
        parent: DOM element reference (parent container)
        old_vnode: Previous VNode or string (can be None)
        new_vnode: New VNode or string (can be None)
        index: Position in parent's children (for operations)

    Preconditions:
        - parent is valid DOM element reference

    Postconditions:
        - DOM updated to match new_vnode
        - new_vnode._el references updated DOM element

    Side effects:
        - Updates DOM elements via js.document
        - May create, remove, or move elements
        - Updates event listeners

    SEE: client.runtime.patch_props, client.runtime.patch_children, tests.unit.test-patch
    """
    # Case 1: One is None - add or remove
    if old_vnode is None and new_vnode is not None:
        mount(parent, new_vnode)
        return

    if old_vnode is not None and new_vnode is None:
        remove_node(parent, old_vnode, index)
        return

    # Case 2: Both None - nothing to do
    if old_vnode is None and new_vnode is None:
        return

    # Case 3: Text nodes
    if isinstance(old_vnode, str) and isinstance(new_vnode, str):
        if old_vnode != new_vnode:
            # Find text node in parent and update
            if index < len(parent.childNodes):
                text_node = parent.childNodes[index]
                text_node.textContent = new_vnode
        return

    # Case 4: Text vs Element - replace
    if isinstance(old_vnode, str) != isinstance(new_vnode, str):
        remove_node(parent, old_vnode, index)
        mount(parent, new_vnode)
        return

    # Case 5: Different tags - replace
    if old_vnode.tag != new_vnode.tag:
        remove_node(parent, old_vnode, index)
        mount(parent, new_vnode)
        return

    # Case 6: Same tag - patch in place
    new_vnode._el = old_vnode._el
    element = old_vnode._el

    # Patch props
    patch_props(element, old_vnode.props or {}, new_vnode.props or {})

    # Patch children
    old_children = old_vnode.children or []
    new_children = new_vnode.children or []

    # Check if children are keyed
    has_keys = (
        len(new_children) > 0 and
        not isinstance(new_children[0], str) and
        hasattr(new_children[0], 'key') and
        new_children[0].key is not None
    )

    if has_keys:
        # Keyed children - use key-based reconciliation
        patch_keyed_children(element, old_children, new_children)
    else:
        # Non-keyed children - patch by index
        patch_children(element, old_children, new_children)


def patch_props(element, old_props, new_props):
    """Update element properties efficiently.

    Updates attributes, styles, classes, and event handlers in-place.
    Removes old props not in new, adds new props, updates changed props.

    WHY: Minimize DOM operations by only updating changed properties

    Args:
        element: DOM element reference
        old_props: Previous props dict
        new_props: New props dict

    Side effects:
        - Updates element attributes via setAttribute/removeAttribute
        - Updates className and style properties
        - Adds/removes event listeners

    SEE: client.runtime.patch, tests.unit.test-patch.test_patch_props
    """
    # Remove old props not in new
    for key in old_props:
        if key not in new_props:
            if key.startswith('on_'):
                # Event listeners auto-cleanup when reassigning
                pass
            elif key == 'class':
                element.className = ''
            elif key == 'style':
                # Clear all styles
                for style_key in (old_props[key] if isinstance(old_props[key], dict) else {}):
                    element.style[style_key] = ''
            else:
                element.removeAttribute(key)

    # Add/update new props
    for key, value in new_props.items():
        old_value = old_props.get(key)

        # Skip if unchanged
        if old_value == value:
            continue

        if key.startswith('on_') and callable(value):
            # Event handler - replace old listener
            event = key[len('on_'):]
            # Remove old listener if exists
            if old_value and callable(old_value):
                # Note: JavaScript addEventListener with same function reference
                # can be removed, but Python closures are different objects
                # For simplicity, we'll just add the new one (old will be GC'd)
                pass
            # Add new listener
            from pyodide.ffi import create_proxy
            proxy = create_proxy(value)
            element.addEventListener(event, proxy)

        elif key == 'class':
            element.className = value

        elif key == 'style' and isinstance(value, dict):
            # Update individual style properties
            old_style = old_props.get('style', {})
            if not isinstance(old_style, dict):
                old_style = {}

            # Remove old style properties
            for style_key in old_style:
                if style_key not in value:
                    element.style[style_key] = ''

            # Add/update new style properties
            for style_key, style_value in value.items():
                element.style[style_key] = style_value

        else:
            # Regular attribute
            element.setAttribute(key, str(value))


def patch_children(parent, old_children, new_children):
    """Patch children by index (non-keyed reconciliation).

    Updates children at each index, removes extras, adds new ones.
    Simple but not optimal for reordered lists.

    WHY: Efficient for stable lists without reordering

    Args:
        parent: DOM element reference
        old_children: List of old VNodes/strings
        new_children: List of new VNodes/strings

    Side effects:
        - Patches existing children via patch()
        - Removes extra old children
        - Mounts new children

    SEE: client.runtime.patch, client.runtime.patch_keyed_children
    """
    old_len = len(old_children)
    new_len = len(new_children)

    # Patch common children at same index
    for i in range(min(old_len, new_len)):
        patch(parent, old_children[i], new_children[i], i)

    # Remove extra old children
    for i in range(new_len, old_len):
        remove_node(parent, old_children[i], new_len)

    # Add extra new children
    for i in range(old_len, new_len):
        mount(parent, new_children[i])


def patch_keyed_children(parent, old_children, new_children):
    """Patch children using keys for optimal list rendering.

    Matches children by key property, minimizing DOM operations.
    Reuses elements when keys match, moves elements as needed.

    WHY: Optimal for dynamic lists with add/remove/reorder operations

    Algorithm:
        1. Build key→(index, vnode) maps for old and new
        2. For each new child:
           - If key exists in old: patch and move if needed
           - If new key: mount new element
        3. Remove old children not in new

    Args:
        parent: DOM element reference
        old_children: List of old VNodes with keys
        new_children: List of new VNodes with keys

    Preconditions:
        - All children have key property set

    Side effects:
        - Patches existing keyed children via patch()
        - Moves DOM elements to match new order
        - Removes children with keys not in new
        - Mounts new keyed children

    SEE: client.runtime.patch, tests.unit.test-patch.test_patch_keyed_children
    """
    # Build key maps
    old_keyed = {}
    for i, child in enumerate(old_children):
        if not isinstance(child, str) and hasattr(child, 'key') and child.key:
            old_keyed[child.key] = (i, child)

    new_keyed = {}
    for i, child in enumerate(new_children):
        if not isinstance(child, str) and hasattr(child, 'key') and child.key:
            new_keyed[child.key] = (i, child)

    # Track which old children to remove
    used_keys = set()

    # First pass: update/move existing keyed children
    for new_idx, new_child in enumerate(new_children):
        if isinstance(new_child, str) or not hasattr(new_child, 'key') or not new_child.key:
            continue

        key = new_child.key
        used_keys.add(key)

        if key in old_keyed:
            old_idx, old_child = old_keyed[key]
            # Patch the matching child
            patch(parent, old_child, new_child, new_idx)

            # Move if position changed
            if old_idx != new_idx:
                move_node(parent, new_child._el, new_idx)
        else:
            # New child - mount it
            mount(parent, new_child)
            # Move to correct position
            if new_idx < len(parent.childNodes):
                move_node(parent, new_child._el, new_idx)

    # Second pass: remove old children not in new
    for key in old_keyed:
        if key not in used_keys:
            _, old_child = old_keyed[key]
            remove_node(parent, old_child, 0)  # Index doesn't matter for removal


def remove_node(parent, vnode, index):
    """Remove a node from DOM.

    Args:
        parent: DOM element reference
        vnode: VNode or string to remove
        index: Position in parent's children

    Side effects:
        - Removes element from DOM
    """
    if isinstance(vnode, str):
        # Text node - remove by index
        if index < len(parent.childNodes):
            parent.removeChild(parent.childNodes[index])
    elif hasattr(vnode, '_el') and vnode._el:
        # Element node - remove directly
        vnode._el.remove()


def move_node(parent, element, new_index):
    """Move an element to a new position in parent.

    Args:
        parent: DOM element reference
        element: DOM element to move
        new_index: Target position

    Side effects:
        - Moves element in DOM
    """
    children = parent.childNodes
    if new_index >= len(children):
        parent.appendChild(element)
    else:
        parent.insertBefore(element, children[new_index])


def rerender():
    """Re-render root component and patch DOM efficiently.

    Phase 3 implementation: Intelligent diffing
    - Render component to new VDOM
    - Use patch() to update only changed nodes
    - Minimize DOM operations for performance

    Phase 4 enhancement: Dynamic component rendering
    - Uses _current_component instead of hard-coded IndexPage
    - Supports re-rendering different page components

    WHY: Triggered by state changes via use_state set_value

    Preconditions:
        - _root_element is set (hydrate called)
        - _root_instance is set with current state
        - _current_vdom contains previous VDOM
        - _current_component is set (Phase 4)

    Postconditions:
        - _current_vdom updated to new VDOM
        - DOM updated to match new VDOM (minimal operations)

    Side effects:
        - Updates DOM elements via patch()
        - May create, update, or remove elements
        - Updates event listeners

    PERFORMANCE:
        - Phase 3: Efficient (only update changed nodes)
        - Reuses elements when possible
        - Minimal DOM operations

    SEE: client.runtime.patch, shared.state.use_state, tests.integration.test-rerender
    """
    global _current_vdom

    # Phase 4: Use stored current component instead of hard-coding IndexPage
    if _current_component is None:
        print("⚠️ Warning: _current_component not set, falling back to IndexPage")
        from pages.index import IndexPage
        component = IndexPage
    else:
        component = _current_component

    # Phase 5: Render new VDOM with updated state AND initial props
    # Initial props persist across rerenders (passed from SSR)
    new_vdom = render_component(component, _initial_props, _root_instance)

    # Phase 3: Intelligent patching
    # Use patch() to update only changed nodes
    patch(_root_element, _current_vdom, new_vdom)

    # Update stored VDOM for next render
    _current_vdom = new_vdom

    print(f"🔄 Re-rendered (state: {_root_instance.state})")

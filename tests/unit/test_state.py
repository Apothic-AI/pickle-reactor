# ANCHOR: tests.unit.state
# TITLE: Unit tests for state management (ComponentInstance, use_state, render_component)
# ROLE: tests/unit layer
# COVERS: shared.state.ComponentInstance, shared.state.use_state, shared.state.render_component
# SCENARIOS: State initialization, set_value updates, multiple hooks, hook ordering

"""
Unit tests for state management in pickle-reactor framework.

This test suite validates:
- ComponentInstance creation and state tracking
- use_state hook initialization and updates
- render_component hook context management
- Multiple use_state calls in single component
- set_value triggers schedule_update callback

STRATEGY:
Pure Python unit tests (Tier 1) - fast, no Pyodide dependency
Test all edge cases and error conditions
"""

import pytest
from shared.state import (
    ComponentInstance,
    use_state,
    render_component,
    _current_instance,
)
from shared.vdom import div, p, button


class TestComponentInstance:
    """Test ComponentInstance class for managing component state."""

    def test_initialization(self):
        """ComponentInstance initializes with empty state and zero hook index."""
        inst = ComponentInstance()
        assert inst.state == []
        assert inst.hook_index == 0
        assert inst.schedule_update is None

    def test_state_array_tracks_multiple_values(self):
        """ComponentInstance.state can hold multiple state values."""
        inst = ComponentInstance()
        inst.state.append(0)
        inst.state.append("test")
        inst.state.append({"key": "value"})

        assert len(inst.state) == 3
        assert inst.state[0] == 0
        assert inst.state[1] == "test"
        assert inst.state[2] == {"key": "value"}

    def test_hook_index_tracks_position(self):
        """ComponentInstance.hook_index tracks current hook position."""
        inst = ComponentInstance()
        assert inst.hook_index == 0

        inst.hook_index += 1
        assert inst.hook_index == 1

        inst.hook_index += 1
        assert inst.hook_index == 2


class TestUseState:
    """Test use_state hook for component state management."""

    def test_use_state_requires_current_instance(self):
        """use_state raises RuntimeError when called outside component render."""
        # Ensure no current instance is set
        import shared.state
        shared.state._current_instance = None

        with pytest.raises(RuntimeError, match="use_state called outside component render"):
            use_state(0)

    def test_use_state_initializes_with_value(self):
        """use_state initializes with provided value."""
        import shared.state
        inst = ComponentInstance()
        shared.state._current_instance = inst

        count, set_count = use_state(0)

        assert count == 0
        assert len(inst.state) == 1
        assert inst.state[0] == 0
        assert inst.hook_index == 1  # Incremented after call

    def test_use_state_initializes_with_callable(self):
        """use_state calls initial value if it's callable."""
        import shared.state
        inst = ComponentInstance()
        shared.state._current_instance = inst

        def get_initial():
            return 42

        count, set_count = use_state(get_initial)

        assert count == 42
        assert inst.state[0] == 42

    def test_set_value_updates_state(self):
        """set_value callable updates state array at correct index."""
        import shared.state
        inst = ComponentInstance()
        shared.state._current_instance = inst

        count, set_count = use_state(0)
        set_count(42)

        assert inst.state[0] == 42

    def test_set_value_triggers_schedule_update(self):
        """set_value calls schedule_update when defined."""
        import shared.state
        inst = ComponentInstance()
        shared.state._current_instance = inst

        update_called = []

        def mock_schedule_update():
            update_called.append(True)

        inst.schedule_update = mock_schedule_update

        count, set_count = use_state(0)
        set_count(1)

        assert len(update_called) == 1

    def test_multiple_use_state_calls_track_separate_slots(self):
        """Multiple use_state calls in same component track separate state slots."""
        import shared.state
        inst = ComponentInstance()
        shared.state._current_instance = inst

        count, _ = use_state(0)
        name, _ = use_state("Alice")
        active, _ = use_state(True)

        assert inst.state[0] == 0
        assert inst.state[1] == "Alice"
        assert inst.state[2] is True
        assert inst.hook_index == 3

    def test_use_state_preserves_state_across_renders(self):
        """use_state returns existing state on subsequent calls."""
        import shared.state
        inst = ComponentInstance()

        # First render
        shared.state._current_instance = inst
        inst.hook_index = 0
        count1, set_count1 = use_state(0)
        set_count1(5)

        # Second render (reset hook_index)
        shared.state._current_instance = inst
        inst.hook_index = 0
        count2, set_count2 = use_state(0)  # Initial value ignored

        assert count2 == 5  # Preserved from first render
        assert inst.state[0] == 5


class TestRenderComponent:
    """Test render_component function for managing hook context."""

    def test_render_component_sets_current_instance(self):
        """render_component sets global _current_instance during render."""
        import shared.state

        def TestComponent(props):
            # Verify _current_instance is set
            assert shared.state._current_instance is not None
            return div({}, "Test")

        inst = ComponentInstance()
        render_component(TestComponent, {}, inst)

    def test_render_component_clears_current_instance(self):
        """render_component clears _current_instance after render."""
        import shared.state

        def TestComponent(props):
            return div({}, "Test")

        inst = ComponentInstance()
        render_component(TestComponent, {}, inst)

        # Should be cleared after render
        assert shared.state._current_instance is None

    def test_render_component_resets_hook_index(self):
        """render_component resets hook_index to 0 before render."""
        def TestComponent(props):
            count1, _ = use_state(0)
            count2, _ = use_state(1)
            return div({}, f"{count1}, {count2}")

        inst = ComponentInstance()

        # First render
        vnode1 = render_component(TestComponent, {}, inst)
        assert inst.hook_index == 2

        # Second render (hook_index should reset)
        vnode2 = render_component(TestComponent, {}, inst)
        assert inst.hook_index == 2  # Same as first render

    def test_render_component_passes_props(self):
        """render_component passes props to component function."""
        def TestComponent(props):
            name = props.get("name", "World")
            return div({}, f"Hello, {name}")

        inst = ComponentInstance()
        vnode = render_component(TestComponent, {"name": "Pickle"}, inst)

        # Verify component received props
        assert vnode.children[0] == "Hello, Pickle"

    def test_render_component_returns_vnode(self):
        """render_component returns VNode from component function."""
        def TestComponent(props):
            return div({"class": "test"}, "Content")

        inst = ComponentInstance()
        vnode = render_component(TestComponent, {}, inst)

        assert vnode.tag == "div"
        assert vnode.props["class"] == "test"
        assert vnode.children[0] == "Content"

    def test_render_component_with_use_state(self):
        """render_component works with use_state hook."""
        def CounterComponent(props):
            count, set_count = use_state(0)
            return div({},
                p({}, f"Count: {count}"),
                button({}, "Increment")
            )

        inst = ComponentInstance()
        vnode = render_component(CounterComponent, {}, inst)

        # Verify state was initialized
        assert inst.state[0] == 0

        # Verify VNode structure
        assert vnode.tag == "div"
        assert len(vnode.children) == 2
        assert vnode.children[0].tag == "p"


class TestIntegrationScenarios:
    """Integration tests for state management scenarios."""

    def test_counter_component_pattern(self):
        """Test complete counter component with state updates."""
        def Counter(props):
            count, set_count = use_state(0)

            return div({"class": "counter"},
                p({}, f"Count: {count}"),
                button({}, "Increment")
            )

        inst = ComponentInstance()

        # First render
        vnode1 = render_component(Counter, {}, inst)
        assert inst.state[0] == 0

        # Simulate state update directly on instance
        inst.state[0] = 1

        # Second render
        vnode2 = render_component(Counter, {}, inst)

        # Verify count updated in VNode
        assert "Count: 1" in str(vnode2.children[0].children[0])

    def test_multiple_state_values_component(self):
        """Test component with multiple state values."""
        def Form(props):
            name, set_name = use_state("")
            email, set_email = use_state("")
            submitted, set_submitted = use_state(False)

            return div({},
                p({}, f"Name: {name}"),
                p({}, f"Email: {email}"),
                p({}, f"Submitted: {submitted}")
            )

        inst = ComponentInstance()
        vnode = render_component(Form, {}, inst)

        assert inst.state == ["", "", False]
        assert inst.hook_index == 3

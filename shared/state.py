# ANCHOR: shared.state
# TITLE: State management implementation (ComponentInstance, use_state, render_component)
# ROLE: state/hooks layer
# EXPORTS: ComponentInstance, use_state, render_component
# SEE: client.runtime.hydrate, tests.unit.test-state, RESEARCH.md section 5

"""
State management module for pickle-reactor framework.

This module provides React-style hooks for component state management:
- ComponentInstance: Tracks state array and hook index for a component
- use_state(initial): Hook for managing component state
- render_component(fn, props, instance): Renders component with hook context

INVARIANTS:
- use_state must be called during component render
- hook_index resets to 0 before each render
- State array grows monotonically (never shrinks)
- schedule_update must be set by runtime before use_state triggers updates

SEE: RESEARCH.md section 5 - State Management Patterns for Python
"""

from typing import Any, Callable, Tuple, Optional


# ANCHOR: shared.state.current-instance
# Global variable tracking current rendering component instance
# Set by render_component, used by hooks like use_state
_current_instance: Optional['ComponentInstance'] = None


class ComponentInstance:
    """Component instance with hook state tracking.

    Each component instance maintains:
    - state: Array of state values from use_state calls
    - hook_index: Current position in state array
    - schedule_update: Callback to trigger re-render (set by runtime)

    INVARIANTS:
    - hook_index resets to 0 before each render
    - state array grows monotonically (never shrinks)
    - schedule_update must be set by runtime before use_state

    SEE: shared.state.use_state, client.runtime.hydrate
    """

    def __init__(self):
        """Initialize component instance with empty state."""
        self.state: list[Any] = []
        self.hook_index: int = 0
        self.schedule_update: Optional[Callable[[], None]] = None


def use_state(initial: Any | Callable[[], Any]) -> Tuple[Any, Callable[[Any], None]]:
    """React-style state hook.

    Args:
        initial: Initial value or callable returning initial value

    Returns:
        Tuple of (current_value, set_value_function)

    Preconditions:
        - Must be called inside component during render
        - _current_instance must be set by render_component

    Postconditions:
        - hook_index incremented by 1
        - state array contains value at current index
        - set_value triggers schedule_update if defined

    Raises:
        RuntimeError: If called outside component render context

    Examples:
        >>> def Counter(props):
        ...     count, set_count = use_state(0)
        ...     return button({"on_click": lambda: set_count(count + 1)}, f"Count: {count}")

    CALLERS: Any component function during render
    SEE: shared.state.ComponentInstance, shared.state.render_component, tests.unit.test-state
    """
    inst = _current_instance
    if inst is None:
        raise RuntimeError("use_state called outside component render")

    idx = inst.hook_index

    # Initialize state on first call at this index
    if idx >= len(inst.state):
        value = initial() if callable(initial) else initial
        inst.state.append(value)

    def set_value(new: Any) -> None:
        """Update state and trigger re-render.

        WHY: Trigger re-render via runtime's schedule_update callback

        Args:
            new: New state value

        SEE: client.runtime.rerender
        """
        inst.state[idx] = new
        if inst.schedule_update:
            inst.schedule_update()

    value = inst.state[idx]
    inst.hook_index += 1
    return value, set_value


def render_component(component_fn: Callable[[dict], Any], props: dict, instance: ComponentInstance) -> Any:
    """Render component with hook context.

    Sets up global _current_instance to enable hooks like use_state,
    resets hook_index to 0, calls component function, then cleans up context.

    Args:
        component_fn: Component function to render (takes props dict)
        props: Properties to pass to component
        instance: ComponentInstance to use for state tracking

    Returns:
        VNode returned by component_fn

    Preconditions:
        - component_fn is callable that takes props dict
        - instance is initialized ComponentInstance

    Postconditions:
        - _current_instance is cleared (None)
        - instance.hook_index is reset for next render
        - Returns VNode from component_fn

    Examples:
        >>> inst = ComponentInstance()
        >>> vnode = render_component(IndexPage, {}, inst)

    SEE: shared.state.use_state, client.runtime.rerender, server.app.home
    """
    global _current_instance

    # Set context for hooks
    _current_instance = instance
    instance.hook_index = 0

    # Call component function
    vnode = component_fn(props)

    # Clear context
    _current_instance = None

    return vnode

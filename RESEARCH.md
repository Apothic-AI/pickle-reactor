# Pickle-Reactor Framework Research

## Executive Summary

This document contains comprehensive research findings for building the "pickle-reactor" framework - a Next.js-style Python framework using Pyodide, PyScript's pydom, and a Python VDOM + state system.

---

## 1. Pyodide Best Practices

### Performance Characteristics
- **Baseline:** 1-16x slower than native Python, acceptable for UI work
- **Optimization Strategies:**
  - Use micropip for package loading
  - CDN distribution for Pyodide core
  - Lazy-load modules only when needed
  - Pre-compile Python to .pyc where possible

### Module Loading Patterns
- **micropip:** Standard package installer for Pyodide
- **loadPackage:** For built-in packages
- **Custom wheels:** For proprietary code
- **Best Practice:** Load core dependencies at startup, lazy-load features

### Async Constraints
- **Event Loop Behavior:** Never block the event loop
- **Minimum Delay:** 4ms minimum on `await asyncio.sleep(0)`
- **Threading:** No threading support - async only
- **Gotcha:** Synchronous Python code can block UI updates

### Memory Management
- **Critical:** Explicitly destroy PyProxy objects to prevent memory leaks
- **Pattern:** Use `proxy.destroy()` after use
- **Web Workers:** Use for isolation and complete memory cleanup
- **GC:** JavaScript GC handles Python objects, but cross-boundary references need manual management

### Bundle Size Optimization
- **Core Pyodide:** ~6-8MB gzipped
- **Strategy:** Load only required stdlib modules
- **Compression:** Use Brotli over gzip (better compression)
- **Caching:** Aggressive CDN caching with cache-busting

### Common Gotchas
1. **Package Availability:** Not all PyPI packages work in Pyodide
2. **Event Handler Bridging:** Python callbacks need special handling in JS
3. **Stdlib Modules:** Not fully loaded by default - explicit loading required
4. **File System:** Virtual file system with limitations
5. **Network:** Must use `fetch` API, no traditional sockets

### Browser Compatibility
- **Chrome/Edge:** Best support, fastest WASM execution
- **Firefox:** Good support, slightly slower WASM
- **Safari:** WebAssembly quirks, test thoroughly
- **Mobile:** Performance varies significantly

---

## 2. PyScript pydom API

### Core API Patterns
- **Pythonic wrapper:** Clean abstraction over JavaScript FFI
- **Query Pattern:** `pydom["#selector"]` for element selection
- **Create Pattern:** `pydom.create("tag")` for element creation
- **Modify Pattern:** Direct attribute/property access

### DOM Manipulation
```python
# Query
elements = pydom["#root"]
element = elements[0]

# Create
div = pydom.create("div")
div.html = "Hello"

# Modify
div.add_class("active")
div.style["color"] = "red"

# Events
def handle_click(event):
    print("clicked")
element.on("click", handle_click)
```

### Capabilities and Limitations
- **Good for:** Common DOM operations, event handling, attribute manipulation
- **Limited:** Complex animations, high-frequency updates
- **Workaround:** Use `js.document` directly for performance-critical paths

### Stability Concerns
- **Status:** Currently unstable with frequent breaking changes
- **Versioning:** Lock to specific PyScript version
- **Alternative:** Consider abstracting behind internal API
- **Recommendation:** Use but prepare for API changes

### Performance Comparison
- **pydom:** Convenient, ~20-30% slower than direct FFI
- **js.document:** Fastest, more verbose
- **Strategy:** pydom for normal ops, direct FFI for hot paths

---

## 3. VDOM Diffing Algorithms

### React Fiber Overview
- **Approach:** Incremental rendering with priority scheduling
- **Complexity:** High (handles concurrent rendering, suspense)
- **Performance:** Excellent but complex implementation
- **Suitability:** Overkill for pickle-reactor MVP

### Preact Simplified Approach
- **Algorithm:** O(n) single-pass diffing
- **Key Features:**
  - Same-level comparison only
  - Key-based reconciliation for lists
  - Simple node replacement when types differ
- **Performance:** Good enough for most use cases
- **Suitability:** **Recommended for pickle-reactor**

### SolidJS Fine-Grained Reactivity
- **Approach:** No VDOM, signals with automatic dependency tracking
- **Performance:** Faster than VDOM (no diffing overhead)
- **Complexity:** Different mental model
- **Suitability:** Consider for Phase 2+ optimization

### Key-Based Reconciliation
- **Purpose:** Optimize list updates
- **Pattern:** Assign unique `key` prop to list items
- **Algorithm:** Match old/new children by key, minimize DOM ops
- **Implementation:** Essential for dynamic lists

### Recommended Implementation
```python
def patch(parent, old_vnode, new_vnode):
    # Type changed → replace
    if type(old_vnode) != type(new_vnode):
        replace_node(parent, old_vnode, new_vnode)
        return

    # Text node → update
    if isinstance(new_vnode, str):
        if old_vnode != new_vnode:
            old_vnode._el.textContent = new_vnode
        return

    # Same tag → patch in place
    if old_vnode.tag == new_vnode.tag:
        patch_props(old_vnode._el, old_vnode.props, new_vnode.props)
        patch_children(old_vnode._el, old_vnode.children, new_vnode.children)
        new_vnode._el = old_vnode._el
    else:
        replace_node(parent, old_vnode, new_vnode)
```

---

## 4. Python SSR Frameworks

### FastHTML
- **Design:** Modern, HTMX-integrated, deferred serialization
- **Pros:** Clean API, good HTMX integration, active development
- **Cons:** Tied to HTMX patterns
- **Pattern:**
```python
from fasthtml.common import *

def HomePage():
    return Div(
        H1("Welcome"),
        P("Hello world")
    )
```

### htpy
- **Design:** Functional API with excellent type safety
- **Pros:** Clean syntax, great IDE support, minimal magic
- **Cons:** Less mature ecosystem
- **Pattern:**
```python
from htpy import div, h1, p

def HomePage():
    return div[
        h1["Welcome"],
        p["Hello world"]
    ]
```
- **Recommendation:** **Best pattern for pickle-reactor components**

### dominate
- **Design:** Context managers for element nesting
- **Pros:** Mature, simple, reliable
- **Cons:** Verbose syntax, less intuitive
- **Pattern:**
```python
from dominate.tags import div, h1, p

def HomePage():
    with div() as root:
        h1("Welcome")
        p("Hello world")
    return root
```

### Comparison and Recommendation
- **Syntax:** htpy > FastHTML > dominate
- **Type Safety:** htpy > FastHTML > dominate
- **Maturity:** dominate > FastHTML > htpy
- **HTMX Integration:** FastHTML > htpy > dominate
- **Pickle-Reactor Fit:** **htpy-inspired functional API**

### Integration with ASGI
```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def home():
    vnode = HomePage()
    html = render_to_string(vnode)
    return f"<!doctype html><html><body>{html}</body></html>"
```

### Security: HTML Escaping
- **Critical:** Always escape user input
- **Pattern:** Use `html.escape()` for text content
- **Exception:** Explicitly trusted HTML (sanitize first)
```python
from html import escape as esc

def render_text(text):
    return esc(str(text))
```

---

## 5. State Management Patterns for Python

### Observable Patterns (RxPY)
- **Approach:** Reactive streams, RxJS-style
- **Pros:** Powerful composition, async-friendly
- **Cons:** Overkill for simple UI state, steep learning curve
- **Suitability:** Not recommended for pickle-reactor

### Signal-Based Reactivity (reaktiv)
- **Approach:** Fine-grained reactivity with automatic dependency tracking
- **Pros:** Automatic updates, efficient, clean API
- **Cons:** Additional dependency
- **Pattern:**
```python
from reaktiv import Signal

count = Signal(0)

def increment():
    count.value += 1

# Auto-updates when count changes
@computed
def doubled():
    return count.value * 2
```
- **Recommendation:** **Best for component state in pickle-reactor**

### Hook-Based State (React-style)
- **Approach:** useState pattern from React
- **Pros:** Familiar to React developers, simple mental model
- **Cons:** More boilerplate than signals
- **Pattern:**
```python
_current_instance = None

def use_state(initial):
    inst = _current_instance
    idx = inst.hook_index

    if idx >= len(inst.state):
        inst.state.append(initial)

    def set_value(new):
        inst.state[idx] = new
        inst.schedule_update()

    value = inst.state[idx]
    inst.hook_index += 1
    return value, set_value
```
- **Recommendation:** **Good for MVP, matches React patterns**

### Immutable State (dataclasses)
- **Approach:** Frozen dataclasses for predictable state
- **Pros:** Simple, type-safe, no surprises
- **Cons:** Verbose for frequent updates
- **Pattern:**
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class AppState:
    user: str
    count: int

# Update via copy
new_state = dataclass.replace(state, count=state.count + 1)
```
- **Recommendation:** **Best for global/shared state**

### Recommendation for Pickle-Reactor
- **Component State:** Hook-based `use_state()` for MVP (familiar pattern)
- **Global State:** Frozen dataclasses (simple, type-safe)
- **Future:** Consider signals (reaktiv) for Phase 2+ optimization

---

## 6. Testing Strategies for Pyodide Code

### Unit Testing Pure Python
- **Approach:** Test VDOM logic in native Python (no Pyodide)
- **Tools:** pytest
- **Benefits:** Fast feedback, easy debugging, CI-friendly
- **Pattern:**
```python
def test_vnode_creation():
    node = h("div", {"class": "box"}, "Hello")
    assert node.tag == "div"
    assert node.props["class"] == "box"
    assert node.children[0] == "Hello"

def test_diff_algorithm():
    old = h("div", {}, "old")
    new = h("div", {}, "new")
    # Test diffing logic
```

### Integration Testing with Pyodide
- **Approach:** pytest with Pyodide loaded in browser
- **Tools:** pytest-pyodide, Playwright
- **Fixture Pattern:**
```python
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="module")
def pyodide_context():
    """Module-scoped Pyodide instance (10-100x faster than per-test)"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8000/test.html")
        page.wait_for_function("window.pyodide !== undefined")
        yield page
        browser.close()

def test_pyodide_integration(pyodide_context):
    result = pyodide_context.evaluate("""
        pyodide.runPython(`
            from myfw import render_component
            # Test Pyodide-specific behavior
        `)
    """)
    assert result == expected
```

### E2E Testing with Playwright
- **Approach:** Full user flows in browser
- **Pattern:**
```python
def test_counter_interaction(page):
    page.goto("http://localhost:8000")
    page.click("button#increment")
    assert page.text_content("#count") == "1"
```

### Performance Testing
- **Metrics:** Bundle size, hydration time, memory usage
- **Tools:** Playwright + Chrome DevTools Protocol
- **Pattern:**
```python
def test_performance_budget(page):
    page.goto("http://localhost:8000")
    metrics = page.evaluate("window.performance.getEntriesByType('navigation')[0]")
    assert metrics["loadEventEnd"] < 1000  # 1s budget
```

### Common Testing Challenges
1. **Memory Leaks:** Pyodide instances don't cleanup properly
   - **Solution:** Module-scoped fixtures, explicit cleanup
2. **Timeouts:** Pyodide loading is slow
   - **Solution:** Increase timeout, module-scoped instance
3. **Browser Differences:** Safari behaves differently
   - **Solution:** Test in multiple browsers, use feature detection
4. **Async Timing:** Race conditions in state updates
   - **Solution:** Use `page.wait_for_function()` for state checks

### Testing Pyramid Strategy
```
      E2E (Few)
     /         \
    /           \
   / Integration \
  /   (Some)      \
 /                 \
/_____Unit_____Many_\
```

- **Many Unit Tests:** Fast, test pure logic
- **Some Integration Tests:** Test Pyodide integration
- **Few E2E Tests:** Critical user flows only

### Recommended Test Structure
```
tests/
  unit/
    test_vdom.py
    test_components.py
    test_state.py
  integration/
    conftest.py  # Pyodide fixtures
    test_rendering.py
    test_events.py
  e2e/
    test_smoke.spec.py
    test_routing.spec.py
```

---

## Key Takeaways

### Critical Insights

1. **Pyodide Performance:** Accept 1-16x slowdown, optimize critical paths with direct FFI
2. **Memory Management:** Explicit PyProxy cleanup essential, use Web Workers for isolation
3. **API Stability:** pydom API unstable, abstract behind internal interface
4. **Diffing Strategy:** Preact-style O(n) algorithm sufficient for MVP
5. **State Management:** Hook-based useState for MVP, signals for optimization
6. **Testing:** Module-scoped Pyodide fixtures critical for speed (10-100x faster)
7. **Security:** Always escape HTML, never unpickle untrusted data
8. **Bundle Size:** Core Pyodide ~6-8MB, aggressive caching required

### Anti-Patterns to Avoid

1. **Don't:** Block event loop with synchronous operations
2. **Don't:** Forget to cleanup PyProxy objects (memory leaks)
3. **Don't:** Rely on pydom API staying stable (abstract it)
4. **Don't:** Implement complex diffing algorithm for MVP (Preact approach is enough)
5. **Don't:** Use observables/RxPY for simple UI state (overkill)
6. **Don't:** Per-test Pyodide initialization (too slow, use module scope)
7. **Don't:** Pickle untrusted data (security risk)
8. **Don't:** Skip HTML escaping (XSS vulnerability)

---

## Recommended Approaches for Pickle-Reactor

### 1. API Design
**Recommendation:** htpy-inspired functional API

```python
from myfw import div, h1, p, button

def Counter(props):
    count, set_count = use_state(0)

    return div[
        h1[f"Count: {count}"],
        button(on_click=lambda: set_count(count + 1))["Increment"]
    ]
```

**Rationale:**
- Clean syntax with bracket notation
- Type-safe with IDE support
- Familiar to Python developers
- Easy to read and write

### 2. DOM Access Strategy
**Recommendation:** pydom for normal ops, `js.document` for hot paths

```python
# Normal operations - use pydom
def mount(parent, vnode):
    el = pydom.create(vnode.tag)
    parent.append(el)

# Performance-critical paths - use js.document
def patch_hot_path(element, new_text):
    element._js_el.textContent = new_text  # Direct FFI
```

### 3. State Management
**Recommendation:** Hook-based useState for MVP

```python
# Phase 1-3: Simple hooks
count, set_count = use_state(0)

# Phase 4+: Consider signals for optimization
from reaktiv import Signal
count = Signal(0)
```

### 4. VDOM Diffing
**Recommendation:** Preact-style O(n) algorithm

```python
def patch(parent, old, new):
    # Simple type/tag comparison
    # Key-based list reconciliation
    # In-place prop patching
    pass
```

### 5. SSR Strategy
**Recommendation:** Simple HTML string rendering

```python
def render_to_string(vnode):
    from html import escape as esc
    # Build HTML string with proper escaping
    return f"<{vnode.tag}>{esc(str(content))}</{vnode.tag}>"
```

### 6. Server↔Client Communication
**Recommendation:** JSON for data, never pickle

```python
# Server
@app.post("/api/action")
async def action(data: dict):
    return {"result": process(data)}

# Client
async def call_action(data):
    res = await js.fetch("/api/action", {
        "method": "POST",
        "body": js.JSON.stringify(data)
    })
    return await res.json()
```

### 7. Testing Strategy
**Recommendation:** Pyramid with module-scoped fixtures

```
- Many unit tests (pure Python, fast)
- Some integration tests (Pyodide, module-scoped fixture)
- Few E2E tests (Playwright, critical flows)
```

### 8. Performance Budgets
**Recommendation:** Set and enforce early

```python
# Phase 1 budgets
MAX_BUNDLE_SIZE = 2_000_000  # 2MB
MAX_HYDRATION_TIME = 1_000   # 1s
MAX_MEMORY_USAGE = 50_000_000  # 50MB
```

---

## Security Best Practices

### 1. HTML Escaping
```python
from html import escape as esc

def render_text(text):
    return esc(str(text))  # Always escape user input
```

### 2. Input Validation
```python
from pydantic import BaseModel

class UserInput(BaseModel):
    name: str
    age: int  # Type validation

@app.post("/api/user")
async def create_user(data: UserInput):
    # Validated automatically
    pass
```

### 3. CSP Headers
```python
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'wasm-unsafe-eval'; "
        "connect-src 'self'"
    )
    return response
```

### 4. Never Unpickle Untrusted Data
```python
# DON'T
data = pickle.loads(user_input)  # DANGEROUS

# DO
data = json.loads(user_input)  # Safe
```

---

## Performance Optimization Checklist

- [ ] Use CDN for Pyodide distribution
- [ ] Lazy-load non-critical modules
- [ ] Implement aggressive caching (ServiceWorker)
- [ ] Use Brotli compression over gzip
- [ ] Minimize PyProxy object creation
- [ ] Explicitly destroy PyProxy objects
- [ ] Use direct FFI for hot paths
- [ ] Implement virtual scrolling for long lists
- [ ] Debounce/throttle high-frequency events
- [ ] Profile with Chrome DevTools
- [ ] Monitor bundle size (budget: 2MB)
- [ ] Monitor hydration time (budget: 1s)
- [ ] Monitor memory usage (budget: 50MB)

---

## Next Steps

Based on this research, proceed with:

1. **Agent Creation:** Create `pickle-reactor-dev-agent` with expertise in:
   - Python web frameworks (FastAPI, ASGI)
   - Pyodide constraints and patterns
   - VDOM diffing algorithms
   - Server-side rendering
   - State management hooks
   - Security best practices

2. **Testing Infrastructure:** Set up before Phase 1:
   - `tests/conftest.py` with Pyodide fixtures
   - `tests/unit/test_vdom.py` template
   - `tests/integration/test_rendering.py` template
   - `tests/e2e/test_smoke.spec.py` template

3. **Performance Budgets:** Define in Phase 1:
   - Max bundle size: 2MB
   - Max hydration time: 1s
   - Max memory usage: 50MB

4. **Phase 1 Implementation:** Start with:
   - VNode and h() implementation
   - Simple SSR render_to_string
   - Minimal FastAPI app
   - Pyodide bootstrap pipeline

---

## References and Sources

1. Pyodide Documentation: https://pyodide.org/
2. PyScript Documentation: https://pyscript.net/
3. React Fiber Architecture: https://github.com/acdlite/react-fiber-architecture
4. Preact Source Code: https://github.com/preactjs/preact
5. SolidJS Reactivity: https://www.solidjs.com/docs/latest/api
6. FastHTML: https://fastht.ml/
7. htpy: https://htpy.dev/
8. dominate: https://github.com/Knio/dominate
9. pytest-pyodide: https://github.com/pyodide/pytest-pyodide
10. Playwright Python: https://playwright.dev/python/

---

**Document Version:** 1.0
**Last Updated:** 2025-11-23
**Author:** deep-research-agent for pickle-reactor framework

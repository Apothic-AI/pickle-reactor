// ANCHOR: client.bootstrap
// TITLE: Pyodide bootstrap and loader
// ROLE: client/browser layer
// SEE: server.app.home, RESEARCH.md section 1 - Pyodide Best Practices

/**
 * Pyodide bootstrap script for pickle-reactor framework.
 *
 * This script:
 * - Loads Pyodide from CDN (jsdelivr)
 * - Initializes Python runtime in browser
 * - Logs success message to prove pipeline works
 * - Updates UI to show Pyodide loaded
 *
 * PERFORMANCE:
 * - Pyodide core is ~6-8MB gzipped
 * - CDN caching reduces subsequent loads
 * - Lazy-load additional packages as needed
 *
 * SEE: https://pyodide.org/en/stable/usage/quickstart.html
 */

// Pyodide version to load from CDN
const PYODIDE_VERSION = "0.24.1";
const PYODIDE_CDN_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;

/**
 * Main initialization function
 */
async function main() {
    console.log("🚀 Pickle-Reactor: Starting Pyodide bootstrap...");

    try {
        // Load Pyodide from CDN
        console.log(`📦 Loading Pyodide ${PYODIDE_VERSION} from CDN...`);
        const startTime = performance.now();

        const pyodide = await loadPyodide({
            indexURL: PYODIDE_CDN_URL,
        });

        const loadTime = performance.now() - startTime;
        console.log(`✅ Pyodide loaded in ${loadTime.toFixed(0)}ms`);

        // Test Python execution
        console.log("🐍 Testing Python execution...");
        const result = await pyodide.runPythonAsync(`
# Phase 1 test: Hello from Pyodide
print("Hello from Pyodide in the browser! 🎉")

# Basic Python verification
import sys
f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        `);

        console.log(`🎉 Python execution successful: ${result}`);

        // Store pyodide instance globally for future use
        window.pyodide = pyodide;

        // Phase 2: Load client runtime and hydrate
        console.log("🔧 Phase 2: Loading client runtime...");

        // Load project Python files into Pyodide filesystem
        console.log("📦 Loading pickle-reactor modules...");

        // Create directory structure first (Pyodide FS requires parent directories to exist)
        console.log("  📁 Creating directory structure...");
        pyodide.FS.mkdir('/shared');
        pyodide.FS.mkdir('/client');
        pyodide.FS.mkdir('/pages');
        console.log("  ✓ Directories created");

        // Fetch and write modules to filesystem
        // Phase 4: Added about and todos page modules
        const modules = {
            'shared/vdom.py': await (await fetch('/static/shared_vdom.py')).text(),
            'shared/state.py': await (await fetch('/static/shared_state.py')).text(),
            'shared/__init__.py': '',
            'pages/index.py': await (await fetch('/static/pages_index.py')).text(),
            'pages/about.py': await (await fetch('/static/pages_about.py')).text(),
            'pages/todos.py': await (await fetch('/static/pages_todos.py')).text(),
            'pages/__init__.py': '',
            'client/runtime.py': await (await fetch('/static/client_runtime.py')).text(),
            'client/__init__.py': ''
        };

        // Write modules to Pyodide filesystem
        for (const [path, code] of Object.entries(modules)) {
            pyodide.FS.writeFile('/' + path, code);
            console.log(`  ✓ Loaded ${path}`);
        }

        // Add root directory to Python path
        await pyodide.runPythonAsync(`
import sys
sys.path.insert(0, '/')
print(f"Python path: {sys.path[:3]}")
        `);

        // Initialize client runtime
        console.log("🔧 Initializing client runtime...");

        await pyodide.runPythonAsync(`
# Import client runtime and hydrate
from client.runtime import hydrate

# Start hydration
hydrate()
        `);

        console.log("✅ Client runtime hydrated!");

        // Update UI to show Pyodide loaded
        updateStatusUI(true, loadTime);

        console.log("✨ Pickle-Reactor Phase 2 initialization complete!");

    } catch (error) {
        console.error("❌ Pyodide initialization failed:", error);
        updateStatusUI(false, 0, error.message);
    }
}

/**
 * Update status UI to show Pyodide loading state
 */
function updateStatusUI(loaded, loadTime, errorMessage = null) {
    const statusEl = document.getElementById('pyodide-status');

    if (!statusEl) {
        console.warn("Status element not found");
        return;
    }

    if (loaded) {
        statusEl.className = 'status loaded';
        statusEl.innerHTML = `<p>✅ Pyodide loaded successfully in ${loadTime.toFixed(0)}ms</p>`;
    } else {
        statusEl.className = 'status error';
        statusEl.innerHTML = `<p>❌ Failed to load Pyodide: ${errorMessage}</p>`;
    }
}

// Start initialization when script loads
main();

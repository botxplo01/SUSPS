import threading
import webbrowser
import time

import uvicorn

# Optional dependency; only used when running desktop mode
try:
    import webview
except Exception:  # pragma: no cover
    webview = None


def run_api():
    # Run FastAPI (which also mounts Dash)
    uvicorn.run(
        "src.backend.api:app", host="127.0.0.1", port=8000, reload=False, factory=False
    )


def main():
    server_thread = threading.Thread(target=run_api, daemon=True)
    server_thread.start()

    # Wait a moment for server to come up
    time.sleep(1.5)
    url = "http://127.0.0.1:8000/dash/"

    if webview is None:
        # Fallback: open browser if pywebview is not installed
        webbrowser.open(url)
        print("pywebview not installed. Opened in default browser.")
        server_thread.join()
        return

    # Create native window
    webview.create_window("SUSPS", url)
    webview.start()


if __name__ == "__main__":
    main()

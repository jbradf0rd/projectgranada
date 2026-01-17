"""
Granada v2 - Main Application Entry Point
Offline Arabic Book Search Engine and Personal Library Manager
"""
import sys
import webbrowser
import threading
from app import create_app
from config import Config

app = create_app()


def open_browser():
    """Open the default web browser to the app URL."""
    url = f"http://{Config.HOST}:{Config.PORT}"
    webbrowser.open(url)


if __name__ == '__main__':
    # Determine if running as frozen executable
    is_frozen = getattr(sys, 'frozen', False)

    if is_frozen:
        # Production mode - open browser after short delay
        threading.Timer(1.5, open_browser).start()
        print(f"Starting Granada at http://{Config.HOST}:{Config.PORT}")
        print("Press Ctrl+C to stop the server.")

        # Run without debug, with threading for better performance
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=False,
            threaded=True,
            use_reloader=False
        )
    else:
        # Development mode
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=True
        )

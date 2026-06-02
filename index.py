import os
import sys
import time
import subprocess
import webbrowser
import signal

# Get the absolute paths of the directories
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND2_DIR = os.path.join(ROOT_DIR, "frontend2")

processes = []

def cleanup(sig=None, frame=None):
    print("\n[EcoSort AI] Shutting down backend and frontend servers...")
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=2)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
    print("[EcoSort AI] All servers stopped. Goodbye!")
    sys.exit(0)

# Register shutdown signals
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def main():
    print("[EcoSort AI] Starting EcoSort AI application...")
    
    # 1. Start the Flask backend (runs on port 5000 by default)
    print("[EcoSort AI] Launching Flask backend API...")
    try:
        backend_proc = subprocess.Popen(
            [sys.executable, "app.py"],
            cwd=BACKEND_DIR
        )
        processes.append(backend_proc)
    except Exception as e:
        print(f"[EcoSort AI] Failed to start backend: {e}")
        cleanup()

    # Give the backend server a moment to start
    time.sleep(2)

    # 2. Start the Streamlit frontend (runs on port 8501 by default)
    print("[EcoSort AI] Launching Streamlit frontend...")
    try:
        # Run streamlit as a module using the current python executable
        frontend_proc = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port=8501"],
            cwd=FRONTEND2_DIR
        )
        processes.append(frontend_proc)
    except Exception as e:
        print(f"[EcoSort AI] Failed to start Streamlit: {e}")
        cleanup()

    # Give the frontend server a moment to spin up
    time.sleep(2)
    
    print("\n==================================================")
    print("EcoSort AI is fully running!")
    print("Backend API: http://localhost:5000")
    print("Streamlit Frontend: http://localhost:8501")
    print("==================================================")
    print("Press Ctrl+C in this terminal to stop both servers.\n")

    # Automatically open the browser to the Streamlit app
    try:
        webbrowser.open("http://localhost:8501")
    except Exception:
        pass

    # Monitor subprocesses to keep main thread alive
    try:
        while True:
            # Check if either process terminated unexpectedly
            if backend_proc.poll() is not None:
                print("[EcoSort AI] Warning: Flask backend stopped unexpectedly.")
                break
            if frontend_proc.poll() is not None:
                print("[EcoSort AI] Warning: Streamlit frontend stopped unexpectedly.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()

if __name__ == "__main__":
    main()

# Debugging with PyCharm & Docker Compose

Since you want to run the scraper through Docker Compose but debug it in PyCharm, follow these steps to set up the **Remote Interpreter**.

## 1. Configure Remote Interpreter
1.  Open PyCharm Settings/Preferences (`Ctrl+Alt+S`).
2.  Go to **Project: job-scraper** > **Python Interpreter**.
3.  Click **Add Interpreter** > **On Docker Compose...**
4.  **Server**: Select `Docker`.
5.  **Configuration files**: Select `docker/docker-compose.yml`.
6.  **Service**: Select `scraper-worker`.
7.  Click **Next/Create**.
    *   PyCharm will spin up the containers and introspect the Python environment.

## 2. Create Run Configuration
1.  Go to **Run** > **Edit Configurations...**
2.  Click **+** and select **Python**.
3.  **Name**: `Debug Worker (Docker)`
4.  **Script path**: Click the folder icon and select `worker/worker.py` (ensure you select it via the project path, PyCharm handles the mapping).
5.  **Working directory**: `/app` (PyCharm might auto-detect `.../job-scraper`, which maps to `/app`).
6.  **Interpreter**: Select the Docker Compose interpreter you just created.
7.  Click **OK**.

## 3. Start Debugging
1.  Open `worker/worker.py`.
2.  Set a **Breakpoint** (click the gutter next to a line number, e.g., inside `process_job`).
3.  Click the **Debug** icon (green bug) for your `Debug Worker (Docker)` configuration.
4.  PyCharm will:
    *   Run `docker-compose up` for you.
    *   Attach the debugger.
    *   Stop at your breakpoint.

## Note on Code Changes
I have updated `docker-compose.yml` to mount your source code (`..:/app`). 
This means you can **edit code in PyCharm**, and when you restart the debugger, the container sees the new code **immediately without rebuilding**.

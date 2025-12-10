---
description: How to deploy the Splay Network application to Render
---

This guide outlines the steps to deploy your Flask application to **Render**, a cloud platform that supports Python web apps easily.

### Prerequisites

1.  **Gunicorn**: We have already added `gunicorn` to your `requirements.txt`. This is the production server required for deployment (app.run is only for development).
2.  **Procfile**: We have created a `Procfile` in your root directory containing `web: gunicorn app:app`. This tells Render how to start your app.
3.  **GitHub Account**: You will need to push your code to a GitHub repository.

### Step-by-Step Deployment

1.  **Push Code to GitHub**:
    *   Initialize a git repository if you haven't already:
        ```bash
        git init
        git add .
        git commit -m "Initial commit for deployment"
        ```
    *   Create a new repository on GitHub.
    *   Link and push your code:
        ```bash
        git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
        git branch -M main
        git push -u origin main
        ```

2.  **Create Service on Render**:
    *   Go to [dashboard.render.com](https://dashboard.render.com/).
    *   Click **New +** and select **Web Service**.
    *   Connect your GitHub account and select the repository you just pushed.

3.  **Configure Build & Start**:
    *   **Name**: Give your service a unique name (e.g., `splay-network-app`).
    *   **Region**: Choose the one closest to you.
    *   **Runtime**: Select **Python 3**.
    *   **Build Command**: `pip install -r requirements.txt`
        *   *Note*: Render requires `numpy<2` compatibility if your code was developed that way. Ensure requirements.txt is accurate.
    *   **Start Command**: `gunicorn app:app` (Render might auto-detect this from the Procfile).
    *   **Free Instance Type**: Select "Free" if just testing.

4.  **Environment Variables**:
    *   If you have any API keys or secrets (not used in this simple demo), add them under the "Environment" tab.
    *   For this app, ensure `PYTHON_VERSION` is set to `3.10.0` or similar if needed, typically default is fine.

5.  **Deploy**:
    *   Click **Create Web Service**.
    *   Render will start building your app. Watch the logs.
    *   Once the build finishes, you will see a green "Live" badge and a URL (e.g., `https://splay-network-app.onrender.com`).

### Troubleshooting

*   **Memory Issues**: The free tier has limited RAM (512MB). If loading PyTorch (Ultralytics) triggers an OOM (Out of Memory) kill, you might need to:
    *   Use a smaller model (we are already using `yolov8n.pt`, the nano version, which is good).
    *   Upgrade to a paid instance.
*   **OpenCV Dependencies**: `opencv-python-headless` is already in requirements, which includes necessary binary dependencies for Linux environments on Render.

### Docker Alternative (Advanced)

If you prefer using Docker, you can add a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
```

If using Docker on Render, choose "Docker" as the runtime instead of Python.

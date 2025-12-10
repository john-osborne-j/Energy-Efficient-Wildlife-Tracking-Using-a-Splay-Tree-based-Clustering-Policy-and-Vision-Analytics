---
description: How to deploy to Hugging Face Spaces (Free & Fast for AI)
---

**Hugging Face Spaces** is widely considered the best free platform for AI demos. It offers faster CPUs and generous RAM (16GB) on the free tier, which is perfect for your specific app (YOLOv8 + DeepSORT).

### Step 1: Create a Space

1.  Go to [huggingface.co/spaces](https://huggingface.co/spaces) and Sign Up/Login.
2.  Click **"Create new Space"**.
3.  **Space Name**: e.g., `splay-network-demo`.
4.  **License**: `MIT` or `OpenRAIL`.
5.  **SDK**: Choose **Docker** (Since we have a complex Flask app with specific system dependencies).
6.  **Privacy**: Public.
7.  Click **"Create Space"**.

### Step 2: Upload Your Code

Hugging Face Spaces are just Git repositories. You can push your existing code directly to it.

1.  **Clone the Space locally** (or add it as a new remote to your existing repo):
    *   *In your current terminal:*
    ```bash
    git remote add space https://huggingface.co/spaces/YOUR_USERNAME/splay-network-demo
    ```
    *(Replace `YOUR_USERNAME` and `splay-network-demo` with actual values)*

2.  **Push to the Space**:
    ```bash
    git push -u space main
    ```
    *   **Important**: When asked for a **Password**, you **MUST** use a Hugging Face **Access Token**, not your account password.
    *   Get a token here: [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens). Make sure to set the role to **"Write"**.

### Step 3: Deployment

*   Hugging Face will detect the `Dockerfile` we just created.
*   It will build the image (this takes 2-3 minutes).
*   Once done, your app will be running on high-performance infrastructure!

### Why this is better than Render for you?
*   **No "Worker Timeouts"**: Designed for AI models that take time to load.
*   **More RAM**: 16GB free vs Render's 512MB. The video feed will be much smoother.
*   **Persistent**: Doesn't "sleep" as aggressively as other free tiers.

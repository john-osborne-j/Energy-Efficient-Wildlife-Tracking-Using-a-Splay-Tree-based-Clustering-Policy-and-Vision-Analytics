document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('simCanvas');
    const ctx = canvas.getContext('2d');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const nodeCountInput = document.getElementById('nodeCount');
    const simTimeEl = document.getElementById('simTime');
    const activeNodesEl = document.getElementById('activeNodes');

    // Dashboard Elements
    const deadCountEl = document.getElementById('deadCount');
    const avgDowntimeEl = document.getElementById('avgDowntime');
    const deadNodesListEl = document.getElementById('deadNodesList');

    let isRunning = false;
    let animationId = null;
    const AREA_SIZE = 1000.0; // Must match backend

    function resizeCanvas() {
        const wrapper = document.getElementById('canvas-wrapper');
        canvas.width = wrapper.clientWidth;
        canvas.height = wrapper.clientHeight;
    }

    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    startBtn.addEventListener('click', async () => {
        if (isRunning) return;

        const n_nodes = parseInt(nodeCountInput.value);
        if (!n_nodes || n_nodes < 1) {
            alert("Please enter a valid number of nodes.");
            return;
        }

        try {
            const res = await fetch('/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ n_nodes: n_nodes })
            });
            const data = await res.json();

            if (data.status === 'ok') {
                isRunning = true;
                startBtn.disabled = true;
                stopBtn.disabled = false;
                startBtn.classList.add('disabled');

                // Reset Dashboard
                if (deadNodesListEl) deadNodesListEl.innerHTML = '';
                if (deadCountEl) deadCountEl.textContent = '0';
                if (avgDowntimeEl) avgDowntimeEl.textContent = '0';

                loop();
            }
        } catch (e) {
            console.error("Error starting simulation:", e);
        }
    });

    stopBtn.addEventListener('click', () => {
        isRunning = false;
        if (animationId) clearTimeout(animationId);
        startBtn.disabled = false;
        stopBtn.disabled = true;
        startBtn.classList.remove('disabled');
    });

    async function loop() {
        if (!isRunning) return;

        try {
            const res = await fetch('/step');
            const state = await res.json();
            draw(state);
            updateDashboard(state);

            simTimeEl.textContent = state.sim_time;
            const liveNodes = state.nodes.filter(n => !n.dead).length;
            activeNodesEl.textContent = liveNodes;

            if (liveNodes === 0 && isRunning) {
                isRunning = false;
                startBtn.disabled = false;
                stopBtn.disabled = true;
                startBtn.classList.remove('disabled');
                return;
            }

            // Throttled loop: 200ms delay ~ 5 FPS
            animationId = setTimeout(loop, 200);
        } catch (e) {
            console.error("Error fetching step:", e);
            isRunning = false;
        }
    }

    function updateDashboard(state) {
        if (!state.dead_stats) return;

        const deadCount = state.dead_stats.length;
        if (deadCountEl) deadCountEl.textContent = deadCount;

        // Calculate Average Downtime
        let totalDowntime = 0;
        state.dead_stats.forEach(s => totalDowntime += s.downtime);
        const avg = deadCount > 0 ? (totalDowntime / deadCount).toFixed(1) : 0;
        if (avgDowntimeEl) avgDowntimeEl.textContent = avg;

        // Populate List (Latest 5 failures?)
        if (deadNodesListEl) {
            // Clear current list to rebuild or append? Rebuilding is safer for sync
            deadNodesListEl.innerHTML = '';

            // Sort by most recent death (highest downtime implies earliest death, wait. 
            // We want recent failures. dead_since is the tick. Higher dead_since = more recent.)
            // let's sort by dead_since descending.
            const sorted = [...state.dead_stats].sort((a, b) => b.dead_since - a.dead_since);

            sorted.slice(0, 10).forEach(stat => {
                const li = document.createElement('li');
                li.className = 'dead-node-item';
                li.innerHTML = `
                    <span class="dead-node-id">Node ${stat.id}</span>
                    <span class="dead-node-time">Down for ${stat.downtime}t (Since: ${stat.dead_since})</span>
                `;
                deadNodesListEl.appendChild(li);
            });
        }
    }

    function draw(state) {
        // Clear background
        ctx.fillStyle = '#0a0a12'; // Or clearRect for transparency if using CSS bg
        ctx.clearRect(0, 0, canvas.width, canvas.height); // Use CSS background

        // Calculate Scale to Fit
        const scaleX = canvas.width / AREA_SIZE;
        const scaleY = canvas.height / AREA_SIZE;
        const scale = Math.min(scaleX, scaleY) * 0.9; // 90% fit
        const offsetX = (canvas.width - AREA_SIZE * scale) / 2;
        const offsetY = (canvas.height - AREA_SIZE * scale) / 2;

        const transform = (x, y) => ({
            x: offsetX + x * scale,
            y: offsetY + y * scale // Flip Y if needed? Matplotlib is cartesian bottom-up, but usually 0,0 is top-left in canvas.
            // In the Python code: (0,0) to (1000, 1000).
            // Matplotlib typically puts (0,0) at bottom-left. Canvas is top-left.
            // If I want to match visual exactly, I might need to invert Y: AREA_SIZE - y.
            // Let's assume standard top-left for now or just check.
            // The python visual uses `ax.set_ylim(0, AREA_SIZE)`, so 0 is bottom.
            // So: y_canvas = offsetY + (AREA_SIZE - y) * scale
        });

        // Helper to transform points
        const t = (x, y) => {
            return {
                x: offsetX + x * scale,
                y: offsetY + (AREA_SIZE - y) * scale
            };
        };

        // Draw Links
        if (state.links) {
            state.links.forEach(link => {
                const start = t(link.start[0], link.start[1]);
                const end = t(link.end[0], link.end[1]);

                ctx.beginPath();
                ctx.moveTo(start.x, start.y);
                ctx.lineTo(end.x, end.y);
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
                ctx.lineWidth = 1;
                ctx.stroke();
            });
        }

        // Draw Gateway
        const gw = t(state.gateway[0], state.gateway[1]);
        ctx.fillStyle = '#00f3ff';
        ctx.shadowColor = '#00f3ff';
        ctx.shadowBlur = 20;
        ctx.beginPath();
        ctx.arc(gw.x, gw.y, 8, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0; // Reset

        // Draw Nodes
        state.nodes.forEach(node => {
            const p = t(node.x, node.y);

            // Outer glow for heads
            if (node.is_head) {
                ctx.beginPath();
                ctx.arc(p.x, p.y, 12, 0, Math.PI * 2);
                ctx.fillStyle = hexToRgba(node.color, 0.2);
                ctx.fill();

                ctx.beginPath();
                ctx.arc(p.x, p.y, 8, 0, Math.PI * 2);
                ctx.strokeStyle = node.color;
                ctx.lineWidth = 2;
                ctx.stroke();
            }

            // Core node
            ctx.beginPath();
            ctx.arc(p.x, p.y, node.is_head ? 6 : 4, 0, Math.PI * 2);
            ctx.fillStyle = node.color;
            ctx.fill();

            // Dead marker
            if (node.dead) {
                ctx.strokeStyle = '#fff';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(p.x - 3, p.y - 3);
                ctx.lineTo(p.x + 3, p.y + 3);
                ctx.moveTo(p.x + 3, p.y - 3);
                ctx.lineTo(p.x - 3, p.y + 3);
                ctx.stroke();
            }
        });
    }

    function hexToRgba(hex, alpha) {
        // Basic hex parsing
        let c;
        if (/^#([A-Fa-f0-9]{3}){1,2}$/.test(hex)) {
            c = hex.substring(1).split('');
            if (c.length === 3) {
                c = [c[0], c[0], c[1], c[1], c[2], c[2]];
            }
            c = '0x' + c.join('');
            return 'rgba(' + [(c >> 16) & 255, (c >> 8) & 255, c & 255].join(',') + ',' + alpha + ')';
        }
        return hex;
    }

    // --- Wildlife Detection Utils ---
    const dropZone = document.getElementById('dropZone');
    const videoInput = document.getElementById('videoInput');
    const uploadStatus = document.getElementById('uploadStatus');
    const videoPlaceholder = document.getElementById('videoPlaceholder');
    const feedWrapper = document.querySelector('.video-feed-wrapper');

    if (dropZone) {
        dropZone.addEventListener('click', () => videoInput.click());

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.style.borderColor = '#00f3ff';
        });

        dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dropZone.style.borderColor = 'rgba(255, 255, 255, 0.1)';
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.style.borderColor = 'rgba(255, 255, 255, 0.1)';
            if (e.dataTransfer.files.length) {
                handleUpload(e.dataTransfer.files[0]);
            }
        });

        videoInput.addEventListener('change', () => {
            if (videoInput.files.length) {
                handleUpload(videoInput.files[0]);
            }
        });
    }

    async function handleUpload(file) {
        if (!file.type.startsWith('video/')) {
            uploadStatus.textContent = "Error: Please upload a video file.";
            uploadStatus.style.color = '#ff4444';
            return;
        }

        uploadStatus.textContent = `Uploading ${file.name}... (This may take a moment)`;
        uploadStatus.style.color = '#8892b0';

        const formData = new FormData();
        formData.append('video', file);

        try {
            const res = await fetch('/upload_video', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();

            if (data.status === 'ok') {
                uploadStatus.textContent = "Processing Started! Stream below.";
                uploadStatus.style.color = '#00ff00';
                startVideoFeed();
            } else {
                uploadStatus.textContent = "Upload Failed: " + (data.error || 'Unknown error');
                uploadStatus.style.color = '#ff4444';
            }
        } catch (e) {
            console.error(e);
            uploadStatus.textContent = "Network Error.";
            uploadStatus.style.color = '#ff4444';
        }
    }

    function startVideoFeed() {
        // Clear placeholder
        if (videoPlaceholder) videoPlaceholder.style.display = 'none';

        // Remove existing img if any
        const existing = document.getElementById('detectionFeed');
        if (existing) existing.remove();

        // Add MJPEG Stream Image
        const img = document.createElement('img');
        img.id = 'detectionFeed';
        img.src = '/video_feed?' + new Date().getTime(); // Cache bust
        feedWrapper.appendChild(img);
    }
});

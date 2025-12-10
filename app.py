from flask import Flask, render_template, jsonify, request, Response
from simulation import Simulation
from detection import VideoProcessor
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

sim = Simulation()
video_processor = VideoProcessor()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_simulation():
    data = request.json
    n_nodes = data.get('n_nodes', 50)
    sim.reset(n_nodes)
    return jsonify({'status': 'ok', 'n_nodes': n_nodes})

@app.route('/step')
def step():
    state = sim.step()
    return jsonify(state)

@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Initialize processor with this video
    video_processor.set_source(filepath)
    
    return jsonify({'status': 'ok', 'filename': filename})

@app.route('/video_feed')
def video_feed():
    return Response(video_processor.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(debug=True, port=5000)

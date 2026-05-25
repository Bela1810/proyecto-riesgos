import logging
import queue

from flask import Flask, jsonify, request
from flask_cors import CORS
from logic import run_estimation_process

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('werkzeug')
log.setLevel(logging.INFO)

log_queue = queue.Queue()

def api_log(message, level="info"):
    if level == "error":
        app.logger.error(message)
    else:
        app.logger.info(message)

    # Send to frontend queue
    log_queue.put({"level": level.upper(), "message": message})

@app.route('/api/logs', methods=['GET'])
def get_logs():
    logs = []
    while not log_queue.empty():
        try:
            logs.append(log_queue.get_nowait())
        except queue.Empty:
            break
    return jsonify(logs)

@app.route('/api/run-estimation', methods=['POST'])
def run_estimation():
    try:
        data = request.get_json()
        if not data or 'input_folder' not in data or 'output_folder' not in data:
            return jsonify({"status": "error", "message": "Faltan las rutas de las carpetas de entrada y salida."}), 400

        input_folder = data['input_folder']
        output_folder = data['output_folder']

        result = run_estimation_process(input_folder, output_folder, api_log)

        return jsonify(result)
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        api_log(f"Error inesperado en el endpoint /api/run-estimation: {e}\n{trace}", "error")
        return jsonify({"status": "error", "message": f"Error interno del servidor: {e}\n\nTraceback:\n{trace}"}), 500

if __name__ == '__main__':
    app.run(debug=False, port=5000)

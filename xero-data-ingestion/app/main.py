import os
from flask import Flask, jsonify, request, abort
from utils import get_logger
from data_pipeline import run_pipeline
from table_loader import load_json_to_table
from functools import wraps
import asyncio

app = Flask(__name__)
logger = get_logger()

def require_api_key(f):
    """
    Decorator to require an API key for accessing certain routes.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        expected_api_key = os.environ.get('EXPECTED_API_KEY')
        if not api_key or api_key != expected_api_key:
            abort(403, description="Forbidden")
        return f(*args, **kwargs)
    return decorated

@app.route('/run', methods=['POST'])
@require_api_key
def trigger_pipeline():
    """
    Triggers the data ingestion and loading pipeline.
    """
    try:
        asyncio.run(run_pipeline())
        load_json_to_table()
        return jsonify({"message": "Pipeline completed successfully and BigQuery tables created"}), 200
    except Exception as e:
        error_message = f"Pipeline error: {str(e)}"
        logger.error(error_message)
        return jsonify({"error": error_message}), 500

@app.route('/', methods=['GET'])
def home():
    """
    Home endpoint to check service status.
    """
    return "Data Fetching Service is running", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
"""
Route per servire il frontend statico
"""

import os
from flask import Blueprint, send_from_directory, current_app

static_bp = Blueprint('static_routes', __name__)

@static_bp.route('/')
def serve_frontend():
    """Serve la homepage del frontend"""
    return send_from_directory(current_app.static_folder, 'index.html')

@static_bp.route('/<path:path>')
def serve_static_files(path):
    """Serve file statici del frontend"""
    try:
        return send_from_directory(current_app.static_folder, path)
    except FileNotFoundError:
        # Se il file non esiste, serve index.html per il routing client-side
        return send_from_directory(current_app.static_folder, 'index.html')

@static_bp.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve asset del frontend (CSS, JS, immagini)"""
    return send_from_directory(
        os.path.join(current_app.static_folder, 'assets'), 
        filename
    )

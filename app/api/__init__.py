"""
API package per Deep Search AI
"""

from .routes import api_bp
from .search_controller import SearchController

__all__ = ['api_bp', 'SearchController']

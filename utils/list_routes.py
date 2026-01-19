"""
Script to list all registered Flask routes.
Run with: python backend/utils/list_routes.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from config import Config

app = create_app(Config)

def list_routes():
    """Print all registered routes."""
    routes = []
    
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
            routes.append({
                'endpoint': rule.endpoint,
                'methods': methods,
                'path': str(rule)
            })
    
    # Sort by path
    routes.sort(key=lambda x: x['path'])
    
    print("\n" + "="*80)
    print(f"{'ENDPOINT':<40} {'METHODS':<20} {'PATH':<40}")
    print("="*80)
    
    for route in routes:
        print(f"{route['endpoint']:<40} {route['methods']:<20} {route['path']:<40}")
    
    print("="*80)
    print(f"Total routes: {len(routes)}\n")

if __name__ == '__main__':
    with app.app_context():
        list_routes()

#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import csv
import os
import json
import socket

# Configuration
STARTING_PORT = 8000
REDIRECT_FILE = "redirect-file.txt"

class RedirectHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Load redirects when the server starts
        self.redirects = {}  # Will be loaded per-request to ensure freshness
        super().__init__(*args, **kwargs)
        
    def load_redirects(self):
        """Load redirects from the text file"""
        redirects = {}
        try:
            with open(REDIRECT_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                        
                    if ',' in line:
                        key, url = line.split(',', 1)
                    else:
                        parts = line.split(None, 1)
                        if len(parts) < 2:
                            continue
                        key, url = parts
                        
                    redirects[key.strip()] = url.strip()
                    
            print(f"Loaded {len(redirects)} redirects")
            return redirects
        except Exception as e:
            print(f"Error loading redirects: {e}")
            return {}
    
    def do_GET(self):
        """Handle GET requests"""
        # Always reload redirects to ensure we have the latest
        self.redirects = self.load_redirects()
        
        # Extract the key from the path (removing leading slash)
        path = self.path.lstrip('/')
        
        # Special case for API endpoint to get redirects as JSON
        if path == "api/redirects":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS
            self.end_headers()
            self.wfile.write(json.dumps(self.redirects).encode())
            return
        
        # Handle root path
        if not path or path == "index.html" or path == "redirect-system.html":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Try to serve the redirect-system.html file if it exists
            try:
                with open("redirect-system.html", "rb") as f:
                    self.wfile.write(f.read())
                    return
            except:
                # Create a simple HTML interface if file doesn't exist
                html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Simple Redirect Server</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    table {{ width: 100%; border-collapse: collapse; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <h1>Simple Redirect Server</h1>
                <p>Loaded {len(self.redirects)} redirects from {REDIRECT_FILE}</p>
                
                <h2>Available Redirects</h2>
                <table>
                    <tr>
                        <th>Key</th>
                        <th>URL</th>
                        <th>Test</th>
                    </tr>
            """
            
            # Add rows for each redirect
            for key, url in self.redirects.items():
                html += f"""
                    <tr>
                        <td>{key}</td>
                        <td>{url}</td>
                        <td><a href="/{key}" target="_blank">Test</a></td>
                    </tr>
                """
                
            html += """
                </table>
                <p>To use a redirect, navigate to: <code>http://localhost:{self.server.server_port}/key</code></p>
                <script>
                    // Automatically reload the page every 10 seconds to get fresh redirects
                    setTimeout(() => {
                        window.location.reload();
                    }, 10000);
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
            return
            
        # Handle static files (js, css, etc)
        if '.' in path and not path in self.redirects:
            try:
                with open(path, 'rb') as f:
                    self.send_response(200)
                    if path.endswith('.css'):
                        self.send_header('Content-type', 'text/css')
                    elif path.endswith('.js'):
                        self.send_header('Content-type', 'application/javascript')
                    elif path.endswith('.html'):
                        self.send_header('Content-type', 'text/html')
                    elif path.endswith('.txt'):
                        self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f.read())
                return
            except:
                pass
            
        # Check if we have a redirect for this key
        if path in self.redirects:
            target_url = self.redirects[path]
            
            # Send a redirect
            self.send_response(302)
            self.send_header('Location', target_url)
            self.end_headers()
        else:
            # Key not found
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"Redirect key '{path}' not found.".encode())

def run_server():
    port = STARTING_PORT
    while True:
        try:
            server_address = ('', port)
            httpd = HTTPServer(server_address, RedirectHandler)
            print(f"Starting server on port {port}")
            print(f"Visit http://localhost:{port} to see all available redirects")
            print(f"Use http://localhost:{port}/key to trigger a redirect")
            httpd.serve_forever()
        except socket.error as e:
            if e.errno == 98 or e.errno == 48:  # Address already in use (Linux=98, macOS=48)
                print(f"Port {port} is already in use, trying port {port+1}")
                port += 1
            else:
                raise

if __name__ == "__main__":
    run_server()
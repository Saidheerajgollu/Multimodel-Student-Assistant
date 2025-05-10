#!/usr/bin/env python3
import http.server
import socketserver
import os

# Set the port
PORT = 8080

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type')
        super().end_headers()

# Set up and start the server
handler = MyHandler
with socketserver.TCPServer(("", PORT), handler) as httpd:
    print(f"Serving frontend at http://localhost:{PORT}")
    print("Press Ctrl+C to stop")
    httpd.serve_forever() 
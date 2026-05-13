from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from datetime import datetime
import sqlite3
import uvicorn
import os
import json

# -----------------------------------
# Database Setup
# -----------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "events.db")

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL
)
""")

conn.commit()

# -----------------------------------
# FastAPI App
# -----------------------------------

app = FastAPI(
    title="Productivity Assistant API"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------
# WebSocket Connections
# -----------------------------------

active_connections = []

# Broadcast message to all clients
async def broadcast(message: str):
    disconnected_clients = []

    for connection in active_connections:
        try:
            await connection.send_text(message)
        except:
            disconnected_clients.append(connection)

    # Remove disconnected clients
    for client in disconnected_clients:
        active_connections.remove(client)

# -----------------------------------
# Pub/Sub WebSocket
# -----------------------------------

subscriptions = {}  # {channel_name: [websocket1, websocket2, ...]}

async def subscribe(channel: str, websocket: WebSocket):
    """Add a client to a channel subscription"""
    if channel not in subscriptions:
        subscriptions[channel] = []
    subscriptions[channel].append(websocket)
    print(f"Client subscribed to channel: {channel}")

async def unsubscribe(channel: str, websocket: WebSocket):
    """Remove a client from a channel subscription"""
    if channel in subscriptions and websocket in subscriptions[channel]:
        subscriptions[channel].remove(websocket)
        print(f"Client unsubscribed from channel: {channel}")
        
        # Clean up empty channels
        if not subscriptions[channel]:
            del subscriptions[channel]

async def publish(channel: str, message: str):
    """Send message to all subscribers of a channel"""
    if channel not in subscriptions:
        return
    
    disconnected_clients = []
    
    for connection in subscriptions[channel]:
        try:
            await connection.send_text(message)
        except:
            disconnected_clients.append(connection)
    
    # Remove disconnected clients
    for client in disconnected_clients:
        subscriptions[channel].remove(client)

# -----------------------------------
# Routes
# -----------------------------------

@app.get("/")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/events")
async def get_events():
    cursor.execute("""
        SELECT id, message, created_at
        FROM events
        ORDER BY created_at DESC
        LIMIT 50
    """)

    rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "message": row[1],
            "created_at": row[2]
        }
        for row in rows
    ]

# -----------------------------------
# Pub/Sub Test UI
# -----------------------------------

@app.get("/test-pubsub")
async def test_pubsub_ui():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pub/Sub Test UI</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 900px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }
            .section {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h2 {
                margin-top: 0;
                color: #333;
                border-bottom: 2px solid #007bff;
                padding-bottom: 10px;
            }
            input, button {
                padding: 10px;
                margin: 5px 0;
                width: 100%;
                border: 1px solid #ddd;
                border-radius: 4px;
                box-sizing: border-box;
                font-size: 14px;
            }
            button {
                background-color: #007bff;
                color: white;
                cursor: pointer;
                border: none;
                margin-top: 10px;
            }
            button:hover {
                background-color: #0056b3;
            }
            #messages {
                height: 300px;
                overflow-y: auto;
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                margin-top: 10px;
            }
            .message {
                padding: 8px;
                margin: 5px 0;
                background-color: #e3f2fd;
                border-left: 4px solid #007bff;
                border-radius: 2px;
                font-size: 12px;
            }
            .message.success {
                background-color: #e8f5e9;
                border-left-color: #4caf50;
            }
            .message.error {
                background-color: #ffebee;
                border-left-color: #f44336;
            }
            .message.received {
                background-color: #fff3e0;
                border-left-color: #ff9800;
            }
            .status {
                padding: 10px;
                margin: 10px 0;
                border-radius: 4px;
                font-weight: bold;
            }
            .status.connected {
                background-color: #c8e6c9;
                color: #2e7d32;
            }
            .status.disconnected {
                background-color: #ffcdd2;
                color: #c62828;
            }
            input[type="text"] {
                margin-bottom: 5px;
            }
        </style>
    </head>
    <body>
        <h1>🔌 Pub/Sub WebSocket Test UI</h1>
        
        <div class="container">
            <!-- Subscriber Section -->
            <div class="section">
                <h2>📥 Subscriber</h2>
                <div id="sub-status" class="status disconnected">Disconnected</div>
                
                <input type="text" id="sub-channel" placeholder="Channel to subscribe (e.g., alerts)" value="alerts">
                <button onclick="subscribeToChannel()">Subscribe</button>
                <button onclick="unsubscribeFromChannel()">Unsubscribe</button>
                <button onclick="connectSubscriber()">Connect</button>
                <button onclick="disconnectSubscriber()">Disconnect</button>
                
                <h3>Messages Received:</h3>
                <div id="messages"></div>
            </div>
            
            <!-- Publisher Section -->
            <div class="section">
                <h2>📤 Publisher</h2>
                <div id="pub-status" class="status disconnected">Disconnected</div>
                
                <input type="text" id="pub-channel" placeholder="Channel to publish (e.g., alerts)" value="alerts">
                <input type="text" id="pub-content" placeholder="Message content" value="Test message">
                <button onclick="publishMessage()">Publish Message</button>
                <button onclick="connectPublisher()">Connect</button>
                <button onclick="disconnectPublisher()">Disconnect</button>
                
                <h3>Activity Log:</h3>
                <div id="messages"></div>
            </div>
        </div>
        
        <div class="section" style="grid-column: 1 / -1;">
            <h2>💬 Activity Log</h2>
            <div id="activity-log"></div>
        </div>

        <script>
            let subWs = null;
            let pubWs = null;
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            
            function log(message, type = 'info') {
                const log = document.getElementById('activity-log');
                const msg = document.createElement('div');
                msg.className = 'message ' + type;
                msg.textContent = '[' + new Date().toLocaleTimeString() + '] ' + message;
                log.appendChild(msg);
                log.scrollTop = log.scrollHeight;
            }
            
            function connectSubscriber() {
                if (subWs && subWs.readyState === WebSocket.OPEN) {
                    log('Subscriber already connected', 'error');
                    return;
                }
                
                const subStatus = document.getElementById('sub-status');
                subWs = new WebSocket(protocol + '//' + window.location.host + '/ws/pubsub');
                
                subWs.onopen = () => {
                    subStatus.textContent = 'Connected ✅';
                    subStatus.className = 'status connected';
                    log('Subscriber connected to WebSocket', 'success');
                };
                
                subWs.onmessage = (event) => {
                    const messagesDiv = document.getElementById('messages');
                    const msg = document.createElement('div');
                    msg.className = 'message received';
                    msg.textContent = event.data;
                    messagesDiv.appendChild(msg);
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                    log('Subscriber received: ' + event.data, 'received');
                };
                
                subWs.onerror = (error) => {
                    log('Subscriber error: ' + error, 'error');
                };
                
                subWs.onclose = () => {
                    subStatus.textContent = 'Disconnected ❌';
                    subStatus.className = 'status disconnected';
                    log('Subscriber disconnected', 'error');
                };
            }
            
            function disconnectSubscriber() {
                if (subWs) {
                    subWs.close();
                }
            }
            
            function subscribeToChannel() {
                if (!subWs || subWs.readyState !== WebSocket.OPEN) {
                    log('Subscriber not connected', 'error');
                    return;
                }
                
                const channel = document.getElementById('sub-channel').value;
                subWs.send(JSON.stringify({
                    action: 'subscribe',
                    channel: channel
                }));
                log('Subscribed to channel: ' + channel, 'success');
            }
            
            function unsubscribeFromChannel() {
                if (!subWs || subWs.readyState !== WebSocket.OPEN) {
                    log('Subscriber not connected', 'error');
                    return;
                }
                
                const channel = document.getElementById('sub-channel').value;
                subWs.send(JSON.stringify({
                    action: 'unsubscribe',
                    channel: channel
                }));
                log('Unsubscribed from channel: ' + channel, 'success');
            }
            
            function connectPublisher() {
                if (pubWs && pubWs.readyState === WebSocket.OPEN) {
                    log('Publisher already connected', 'error');
                    return;
                }
                
                const pubStatus = document.getElementById('pub-status');
                pubWs = new WebSocket(protocol + '//' + window.location.host + '/ws/pubsub');
                
                pubWs.onopen = () => {
                    pubStatus.textContent = 'Connected ✅';
                    pubStatus.className = 'status connected';
                    log('Publisher connected to WebSocket', 'success');
                };
                
                pubWs.onmessage = (event) => {
                    log('Publisher received: ' + event.data, 'info');
                };
                
                pubWs.onerror = (error) => {
                    log('Publisher error: ' + error, 'error');
                };
                
                pubWs.onclose = () => {
                    pubStatus.textContent = 'Disconnected ❌';
                    pubStatus.className = 'status disconnected';
                    log('Publisher disconnected', 'error');
                };
            }
            
            function disconnectPublisher() {
                if (pubWs) {
                    pubWs.close();
                }
            }
            
            function publishMessage() {
                if (!pubWs || pubWs.readyState !== WebSocket.OPEN) {
                    log('Publisher not connected', 'error');
                    return;
                }
                
                const channel = document.getElementById('pub-channel').value;
                const content = document.getElementById('pub-content').value;
                
                pubWs.send(JSON.stringify({
                    action: 'publish',
                    channel: channel,
                    content: content
                }));
                log('Published to ' + channel + ': ' + content, 'success');
            }
        </script>
    </body>
    </html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)

# -----------------------------------
# WebSocket Endpoint
# -----------------------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Add client
    active_connections.append(websocket)

    print("Client connected")

    # Welcome message
    await websocket.send_text("✅ Connected to Productivity Assistant")

    try:
        while True:
            # Receive message
            data = await websocket.receive_text()

            print("Received:", data)

            # Echo back
            await websocket.send_text(f"Echo: {data}")

    except WebSocketDisconnect:
        print("Client disconnected")

        # Remove client
        if websocket in active_connections:
            active_connections.remove(websocket)

# -----------------------------------
# Pub/Sub WebSocket Endpoint
# -----------------------------------

@app.websocket("/ws/pubsub")
async def pubsub_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    subscribed_channels = []
    
    print("Client connected to Pub/Sub")
    
    # Welcome message
    await websocket.send_text("✅ Connected to Pub/Sub. Send: {'action': 'subscribe', 'channel': 'channel_name'}")
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            
            print(f"Pub/Sub received: {data}")
            
            # Parse action (expecting JSON format)
            try:
                msg = json.loads(data)
                action = msg.get("action")
                channel = msg.get("channel")
                content = msg.get("content")
                
                if action == "subscribe" and channel:
                    await subscribe(channel, websocket)
                    subscribed_channels.append(channel)
                    await websocket.send_text(f"✅ Subscribed to {channel}")
                
                elif action == "unsubscribe" and channel:
                    await unsubscribe(channel, websocket)
                    if channel in subscribed_channels:
                        subscribed_channels.remove(channel)
                    await websocket.send_text(f"✅ Unsubscribed from {channel}")
                
                elif action == "publish" and channel and content:
                    await publish(channel, f"📢 [{channel}] {content}")
                    await websocket.send_text(f"✅ Published to {channel}")
                
                else:
                    await websocket.send_text("❌ Invalid action. Use: subscribe, unsubscribe, or publish")
            
            except json.JSONDecodeError:
                await websocket.send_text("❌ Invalid JSON format")
    
    except WebSocketDisconnect:
        print("Pub/Sub client disconnected")
        
        # Unsubscribe from all channels
        for channel in subscribed_channels:
            await unsubscribe(channel, websocket)

# -----------------------------------
# Shutdown Event
# -----------------------------------

@app.on_event("shutdown")
def shutdown_event():
    conn.close()
    print("Database connection closed.")


# -----------------------------------
# Fake Email Notification
# -----------------------------------

@app.post("/fake-email")
async def fake_email():
    timestamp = datetime.utcnow().isoformat()

    message = f"📧 New email received at {timestamp}"

    # Save to database
    cursor.execute(
        "INSERT INTO events (message, created_at) VALUES (?, ?)",
        (message, timestamp)
    )

    conn.commit()

    # Broadcast to WebSocket clients
    await broadcast(message)

    return {
        "status": "success",
        "message": message
    }


# -----------------------------------
# Fake Meeting Notification
# -----------------------------------

@app.post("/fake-meeting")
async def fake_meeting():
    timestamp = datetime.utcnow().isoformat()

    message = f"📅 Meeting reminder at {timestamp}"

    # Save to database
    cursor.execute(
        "INSERT INTO events (message, created_at) VALUES (?, ?)",
        (message, timestamp)
    )

    conn.commit()

    # Broadcast to WebSocket clients
    await broadcast(message)

    return {
        "status": "success",
        "message": message
    }

# -----------------------------------
# Main Entry Point
# -----------------------------------

def main():
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    main()
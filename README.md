# 🚀 Productivity Assistant API

A real-time productivity assistant built with **FastAPI** and **WebSocket** technology. Features a publish-subscribe messaging system for handling notifications and events.

## ✨ Features

- **Real-time WebSocket Communication** - Instant messaging between clients
- **Pub/Sub System** - Subscribe to specific channels for targeted notifications
- **Database Storage** - SQLite database for persistent event logging
- **REST API Endpoints** - HTTP endpoints for triggering notifications
- **Interactive Test UI** - Built-in web interface for testing WebSocket functionality
- **CORS Enabled** - Cross-origin requests supported

## 🛠️ Tech Stack

- **Backend**: Python 3.8+, FastAPI, Uvicorn
- **Database**: SQLite
- **Real-time**: WebSocket
- **Web Framework**: FastAPI
- **Testing**: Built-in HTML test interface

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/productivity-assistant.git
   cd productivity-assistant
   ```

2. **Install dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Run the application**
   ```bash
   cd backend
   python main.py
   ```

The server will start on `http://localhost:8000`

## 🚀 Usage

### WebSocket Endpoints

#### 1. Basic WebSocket (`/ws`)
- Simple echo WebSocket for general communication
- Broadcasts messages to all connected clients

#### 2. Pub/Sub WebSocket (`/ws/pubsub`)
- Advanced publish-subscribe messaging system
- Subscribe to specific channels
- Publish messages to channel subscribers

**Pub/Sub Commands:**
```json
// Subscribe to a channel
{"action": "subscribe", "channel": "alerts"}

// Unsubscribe from a channel
{"action": "unsubscribe", "channel": "alerts"}

// Publish a message to a channel
{"action": "publish", "channel": "alerts", "content": "Server maintenance scheduled"}
```

### REST API Endpoints

#### Health Check
```bash
GET /
```
Returns server status and timestamp.

#### Get Events History
```bash
GET /events
```
Returns last 50 stored events from database.

#### Trigger Fake Notifications
```bash
POST /fake-email
POST /fake-meeting
```
Simulates email/meeting notifications and broadcasts them.

### Test Interface

Visit `http://localhost:8000/test-pubsub` for an interactive WebSocket testing interface with:
- Subscriber panel (connect, subscribe, unsubscribe)
- Publisher panel (connect, publish messages)
- Real-time activity log
- Connection status indicators

## 🔧 API Reference

### WebSocket Endpoints

#### `/ws` - Basic WebSocket
- **Connection**: `ws://localhost:8000/ws`
- **Function**: Echoes back received messages to all clients

#### `/ws/pubsub` - Pub/Sub WebSocket
- **Connection**: `ws://localhost:8000/ws/pubsub`
- **Commands**:
  - `{"action": "subscribe", "channel": "channel_name"}`
  - `{"action": "unsubscribe", "channel": "channel_name"}`
  - `{"action": "publish", "channel": "channel_name", "content": "message"}`

### HTTP Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/events` | Get event history |
| GET | `/test-pubsub` | Test UI |
| POST | `/fake-email` | Trigger email notification |
| POST | `/fake-meeting` | Trigger meeting notification |

## 🧪 Testing

### Using the Built-in Test UI
1. Start the server
2. Open `http://localhost:8000/test-pubsub`
3. Use the subscriber panel to connect and subscribe to channels
4. Use the publisher panel to send messages
5. Watch messages appear in real-time

### Using Python Client
```python
import asyncio
import websockets
import json

async def test_client():
    uri = "ws://localhost:8000/ws/pubsub"
    async with websockets.connect(uri) as websocket:
        # Subscribe to alerts
        await websocket.send(json.dumps({
            "action": "subscribe",
            "channel": "alerts"
        }))

        # Publish a message
        await websocket.send(json.dumps({
            "action": "publish",
            "channel": "alerts",
            "content": "Test message"
        }))

        # Listen for responses
        response = await websocket.recv()
        print(f"Received: {response}")

asyncio.run(test_client())
```

## 📁 Project Structure

```
productivity-assistant/
├── backend/
│   ├── main.py              # Main FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── events.db           # SQLite database (auto-created)
├── README.md               # This file
└── .gitignore             # Git ignore rules
```

## 🔄 How It Works

1. **Client Connection**: Users connect via WebSocket
2. **Channel Subscription**: Clients subscribe to specific channels
3. **Message Publishing**: Publishers send messages to channels
4. **Real-time Delivery**: Messages instantly reach all subscribers
5. **Database Logging**: All events are stored for history

## 🚀 Deployment

### Local Development
```bash
python main.py
```

### Production Deployment
- Use a production ASGI server like Gunicorn
- Set up reverse proxy (nginx)
- Configure environment variables
- Enable SSL/TLS

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - feel free to use this project for learning and development.

## 📞 Contact

- **GitHub**: [YOUR_USERNAME](https://github.com/YOUR_USERNAME)
- **Project**: [Productivity Assistant](https://github.com/YOUR_USERNAME/productivity-assistant)

---

**Built with ❤️ using FastAPI and WebSocket technology**
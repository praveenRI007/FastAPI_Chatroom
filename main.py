from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI()

app.add_middleware(HTTPSRedirectMiddleware)

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <style>
        body {
          margin: 0 auto;
          max-width: 800px;
          padding: 0 20px;
        }
        
        .container {
          border: 2px solid #dedede;
          background-color: #f1f1f1;
          border-radius: 5px;
          padding: 10px;
          margin: 10px 0;
        }
        
        .darker {
          border-color: #ccc;
          background-color: #ddd;
        }
        
        .container::after {
          content: "";
          clear: both;
          display: table;
        }
        
        .container img {
          float: left;
          max-width: 60px;
          width: 100%;
          margin-right: 20px;
          border-radius: 50%;
        }
        
        .container img.right {
          float: right;
          margin-left: 20px;
          margin-right:0;
        }
    </style>
    <body>
        <center>
        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        </center>
        <ul id='messages'>
        </ul>
        
        
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var name = document.getElementById('name')
            document.cookie = "client_id="+name+";"
            var ws = new WebSocket(`ws://localhost:8000/ws/${client_id}`);
            ws.onmessage = function(event) {
            
                //var messages = document.getElementById('messages')
                
                var div_m = document.createElement('div')
                div_m.classList.add('container');
                
                var img_m = document.createElement('img')
                img_m.classList.add('right')
                img_m.style.width = "100%"
                
                var p_m = document.createElement('p')
                
                var content = document.createTextNode(event.data)
                
                div_m.appendChild(img_m)
                div_m.appendChild(p_m)
                p_m.appendChild(content)
                document.body.appendChild(div_m)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            #await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")

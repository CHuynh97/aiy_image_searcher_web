import tornado.web
import tornado.ioloop
import tornado.websocket
import threading
import signal
import json

HOST="localhost"
PORT=8888
WS_ENDPOINT="ws"

class MainHandler(tornado.web.RequestHandler):
    """
    Main class to render homepage of web server.
    """
    def get(self):
        ws_url = f"ws://{HOST}:{PORT}/{WS_ENDPOINT}"
        self.render("templates/index.html", address=ws_url)

class ImageWebSocket(tornado.websocket.WebSocketHandler):
    """
    Class to handle websocket connections from AIY Vision Kit and web browser.
    """
    connected_clients = {}

    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self.client_id = None

    def open(self):
        print("Websocket opened!")
        msg = {"server": "Hello from the server"}
        self.write_message(json.dumps(msg))

    def on_message(self, message):
        message = json.loads(message)
        if "newClient" in message and self.client_id is None:
            new_client = message["newClient"]
            self.connected_clients[new_client] = self
            self.client_id = new_client
            print(f"Established new client: {self.client_id}")
        elif message.get("id", None) == "device":
            try:
                assert "browser" in self.connected_clients, "Browser is disconnected"
                print("Sending image to browser.")
                browser_ws = self.connected_clients["browser"]
                browser_ws.write_message(json.dumps(message))
            except AssertionError:
                # Handle error here if browser disconnected
                print("AssertionError: cannot send image to browser")
            

    def on_close(self):
        self.connected_clients.pop(self.client_id, None)
        print("Client has closed websocket connection.")

def start_server():
    app = tornado.web.Application([
        (r"/", MainHandler),
        (r"/ws", ImageWebSocket)
    ])
    app.listen(PORT)
    print(f"App started on http://localhost:{PORT}")
    print(f"Websocket started on http://localhost:{PORT}/ws")
    tornado.ioloop.IOLoop.current().start()
    print("Exiting server")

def shutdown_server(signum, frame):
    print("Request to shutdown server.")
    ioloop = tornado.ioloop.IOLoop.current()
    ioloop.add_callback_from_signal(ioloop.stop)

def main():
    try:
        signal.signal(signal.SIGINT, shutdown_server)
        start_server()
    except Exception as e:
        pass

if __name__ == '__main__':
    main()
    
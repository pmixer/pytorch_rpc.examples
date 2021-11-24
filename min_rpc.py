# implemented in reference to https://segmentfault.com/a/1190000021599946
# pls split client and server into separate files if you hope so

import sys
import json
import signal
import socket
import argparse

server = None
client = None

def ctrl_c_handler(sig, frame):
  global server
  global client
  if server is not None:
    server.sock.close()
  if client is not None:
    client.sock.close()
  print("\nCtrl+C received, exiting...")
  print("bye!")
  sys.exit(0)

signal.signal(signal.SIGINT, ctrl_c_handler)

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("--mode", type=str, help="type in server or client")
arg_parser.add_argument("--addr", type=str, default="0.0.0.0", help="address of the other side")
arg_parser.add_argument("--port", type=int, default=23333)
args = arg_parser.parse_args()

MAX_DATA_LEN_IN_BYTES = 1024

class Client:
  def __init__(self):
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  def connect(self, addr, port):
    self.sock.connect((addr, port))

  def __getattr__(self, func): # fallback when without the attr?
    def _func(*args, **kwargs): # anonymous method?
      signature = {"func": func, "args": args, "kwargs": kwargs}
      self.sock.send(json.dumps(signature).encode("utf-8"))
      ret_val_in_json = json.loads(self.sock.recv(MAX_DATA_LEN_IN_BYTES).decode("utf-8"))
      return ret_val_in_json["result"]

    setattr(self, func, _func)
    return _func


def saxpy(a, x, y):
  return a * x + y


class Server:
  def __init__(self):
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.supported_functions = {}

  def __exit__(self):
    self.sock.close()

  def register_function(self, function):
    self.supported_functions[function.__name__] = function

  def exec_function(self, signature_in_json):
    # import pdb; pdb.set_trace()
    func = signature_in_json["func"]
    args = signature_in_json["args"]
    kwargs = signature_in_json["kwargs"]

    result = self.supported_functions[func](*args, **kwargs)

    return json.dumps({"result": result})

  def serve(self, port):
    self.sock.bind(("0.0.0.0", int(port)))
    self.sock.listen(5) # 5 seconds?
    while True:
      (client_sock, client_addr) = self.sock.accept()
      received_data = client_sock.recv(MAX_DATA_LEN_IN_BYTES)
      ret_val_in_json = self.exec_function(json.loads(received_data.decode("utf-8")))
      client_sock.sendall(ret_val_in_json.encode("utf-8"))
      client_sock.close()


if __name__ == "__main__":
  if args.mode == "server":
    server = Server()
    server.register_function(saxpy)
    server.serve(args.port)
    server.sock.close()
  elif args.mode == "client":
    client = Client()
    client.connect(args.addr, args.port)
    print("received result: ", client.saxpy(5, 6, 7))
    client.sock.close()
  else:
    print("only server or client mode supported currently")

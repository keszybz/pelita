import sys
import pprint
import zmq
from pelita.messaging.json_convert import json_converter

address = sys.argv[1]

ctx = zmq.Context()
sock = ctx.socket(zmq.SUB)
sock.setsockopt(zmq.SUBSCRIBE, "")
sock.connect(address)
poll = zmq.Poller()
poll.register(sock, zmq.POLLIN)

while True:
    try:
        observed = sock.recv()
        observed = json_converter.loads(observed)
        pprint.pprint(observed)
    except zmq.core.error.ZMQError:
        break

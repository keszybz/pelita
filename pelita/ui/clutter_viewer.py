import logging
import sys
from pprint import pprint

from gi.repository import Clutter, GObject
import zmq

from pelita.viewer import AbstractViewer
from pelita.messaging.json_convert import json_converter
from .clutter_canvas import Canvas

_logger = logging.getLogger('pelita.ui.clutter_viewer')
_logger.setLevel(logging.DEBUG)

def init_clutter():
    "initialize Clutter"
    res, argv = Clutter.init(sys.argv)
    if res != Clutter.InitError.SUCCESS:
        raise ValueError

def subscribe(address):
    ctx = zmq.Context()
    sock = ctx.socket(zmq.SUB)
    sock.setsockopt(zmq.SUBSCRIBE, "")
    sock.connect(address)
    return sock

class Viewer(AbstractViewer):
    def __init__(self, address, controller_address=None, geometry=None):
        if geometry is None:
            geometry = (900, 510)
        super(Viewer, self).__init__(geometry=geometry)
        init_clutter()

        self.canvas = Canvas(geometry=geometry)
        self.socket = subscribe(address)

        self._observe_count = 0

        zmq_fd = self.socket.getsockopt(zmq.FD)
        GObject.io_add_watch(zmq_fd,
                             GObject.IO_IN|GObject.IO_ERR|GObject.IO_HUP,
                             self.zmq_callback, self.socket)

    def run(self):
        Clutter.main()

    def zmq_callback(self, queue, condition, socket):
        print 'zmq_callback', queue, condition, socket

        while socket.getsockopt(zmq.EVENTS) & zmq.POLLIN:
            observed = socket.recv()
            observed = json_converter.loads(observed)
            self.observe(**observed)

        return True

    # def set_initial(self, universe):
    #     self.canvas.create(universe)

    def observe(self, **kwargs): # round_, turn, universe, events):
        self._observe_count += 1
        if self._observe_count == 1:
            print "observed", self._observe_count, kwargs.keys()
            pprint(kwargs)
        # for bot in universe.bots:
        #     self.canvas.move_bot(bot)

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

class Viewer(AbstractViewer):
    def __init__(self, address, controller_address=None, geometry=None):
        if geometry is None:
            geometry = (900, 510)
        super(Viewer, self).__init__(geometry=geometry)
        init_clutter()

        self.canvas = Canvas(geometry=geometry)
        self._init_zmq(address, controller_address)

    def _init_zmq(self, address, controller_address):
        context = zmq.Context()

        print 'listening on', address
        sock = context.socket(zmq.SUB)
        sock.setsockopt(zmq.SUBSCRIBE, "")
        sock.connect(address)

        if controller_address is None:
            self.controller_socket = None
        else:
            print 'dealing on', controller_address
            csock = context.socket(zmq.DEALER)
            csock.connect(controller_address)
            self.controller_socket = csock

        self._observe_count = 0
        self._initialized = False
        zmq_fd = sock.getsockopt(zmq.FD)
        GObject.io_add_watch(zmq_fd,
                             GObject.IO_IN|GObject.IO_ERR|GObject.IO_HUP,
                             self.zmq_callback, sock)
        print 'init done'

    def run(self):
        self.request_initial()
        Clutter.main()

    def request_initial(self):
        print 'request_initial:', self.controller_socket
        if self.controller_socket:
            # TODO: should wait for create message?
            self.controller_socket.send_json({"__action__": "set_initial"})
        return False # done with the callback

    def request_step(self, time):
        # print 'requst_step', time, self.canvas.step_time, self.canvas.paused

        if self.canvas.paused:
            print 'paused'
            self.canvas.unpauser = self.create_request_callbacks
            return False

        if self.controller_socket:
            self.controller_socket.send_json({"__action__": "play_step"})
        wanted = self.canvas.step_time
        if wanted != time:
            self.create_request_callbacks()
            return False # kill this callback
        return True

    def create_request_callbacks(self):
        step_time = self.canvas.step_time
        GObject.timeout_add(int(step_time*1000), self.request_step, step_time)

    def zmq_callback(self, queue, condition, socket):
        # print 'zmq_callback', queue, condition, socket

        while socket.getsockopt(zmq.EVENTS) & zmq.POLLIN:
            message = socket.recv()
            self.message(message)

        return True

    def set_initial(self, universe, **kwargs):
        print 'set_initial!'
        self.canvas.create(universe)
        self._initialized = True
        self.create_request_callbacks()

    def observe(self, universe, game_state):
        # print game_state
        for eaten in game_state.get('food_eaten', []):
            self.canvas.eat_food(tuple(eaten['food_pos']))
        for move in game_state.get('bot_moved', []):
            self.canvas.move_bot(move['bot_id'], move['new_pos'])
        self.canvas.update_score(universe)

    def message(self, message):
        kwargs = json_converter.loads(message)

        self._observe_count += 1
        if self._observe_count <= 0:
            print "message", self._observe_count, kwargs.keys()
            pprint(kwargs)

        action, data = kwargs.get('__action__'), kwargs.get('__data__')
        if action == 'set_initial':
            func = self.set_initial
        elif action == 'observe':
            if self._initialized:
                func = self.observe
            else:
                print 'missed set_initial, falling back to creation upon observe'
                func = self.set_initial
        else:
            print "UNKOWN MESSAGE", action, data
            return

        try:
            func(**data)
        except Exception as e:
            print 'error in callback:', e

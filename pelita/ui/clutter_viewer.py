import logging
import sys

from gi.repository import Clutter

from pelita.viewer import AbstractViewer
from .clutter_canvas import Canvas

_logger = logging.getLogger('pelita.ui.clutter_viewer')
_logger.setLevel(logging.DEBUG)

class Viewer(AbstractViewer):
    def __init__(self, geometry=None):
        super(Viewer, self).__init__(geometry=geometry)
        Clutter.init(sys.argv)
        self.canvas = Canvas(geometry=geometry)

    def set_initial(self, universe):
        self.canvas.create(universe)
        Clutter.main()

    def observe(self, round_, turn, universe, events):
        print "observed", events
        for bot in universe.bots:
            self.canvas.move_bot(bot)

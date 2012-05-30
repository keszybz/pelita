import sys
import glob
import random
from gi.repository import Clutter

from pelita import datamodel

# An easy way to debug clutter and cogl without having to type the
# command line arguments
#DEBUG = True
DEBUG = False
debugArgs = ['--clutter-debug=all', '--cogl-debug=all']

# Define some standard colors to make basic color assigments easier
colorWhite = Clutter.Color.new(255,255,255,255)
colorMuddyBlue = Clutter.Color.new(49,78,108,255)
colorBlack = Clutter.Color.new(0,0,0,255)


BADDIES = glob.glob('/home/zbyszek/python/pelita/sprites/baddies/*.svg')

class Canvas(object):
    def __init__(self, universe):
        mainStage = Clutter.Stage.get_default()
        mainStage.set_color(colorBlack)
        mainStage.set_title("Pelita")
        width, height = universe.maze.width, universe.maze.height
        mainStage.set_size(*self._pos_to_coord(width, height))
        mainStage.set_reactive(True)

        # Create a main layout manager
        mainLayoutManager = Clutter.BoxLayout()
        mainLayoutManager.set_vertical(True)
        mainLayoutManager.set_homogeneous(False)
        mainLayoutManager.set_pack_start(False)
        
        # Create the main window
        # mainStage 
        #  mainWindow :: mainLayoutManager
        mainWindow = Clutter.Box.new(mainLayoutManager)
        mainWindow.set_color(colorBlack)
        mainStage.add_actor(mainWindow)

        # Make the main window fill the entire stage
        mainGeometry = mainStage.get_geometry()
        mainWindow.set_geometry(mainGeometry)

        # Create a rectangle
        self.create_maze(mainWindow, universe)

        self.create_bots(mainWindow, universe)

        # Setup some key bindings on the main stage
        mainStage.connect_after("key-press-event", self.onKeyPress)

        # Present the main stage (and make sure everything is shown)
        mainStage.show_all()

    pixels_per_cell = 30

    def _pos_to_coord(self, col, row):
        ans = (self.pixels_per_cell * col,
               self.pixels_per_cell * row)
        print (col, row), '->', ans
        return ans

    def _create_bot(self, window, bot):
        filename = random.choice(BADDIES)
        print 'bot', bot, 'from', filename
        t = Clutter.Texture(filename=filename)
        width, height = t.get_size()
        if width == 0 or height == 0:
            raise ValueError("failed to load image: '%s'" % filename)
        print t.get_position()
        t.set_size(self.pixels_per_cell, self.pixels_per_cell)
        t.set_position(0, 0)  #*self._pos_to_coord(*bot.current_pos))
        window.add_actor(t)
        print t.get_position()
        return t

    def create_bots(self, window, universe):
        for bot in universe.bots:
            self._create_bot(window, bot)

    def create_maze(self, window, universe):
        # for position, items in universe.maze.iteritems():
        #     model_x, model_y = position
        #     if datamodel.Wall in items:
        #         wall_item = Wall(self.mesh_graph, model_x, model_y)
        #         wall_item.wall_neighbours = []
        #         for dx in [-1, 0, 1]:
        #             for dy in [-1, 0, 1]:
        #                 try:
        #                     if datamodel.Wall in universe.maze[model_x + dx, model_y + dy]:
        #                         wall_item.wall_neighbours.append( (dx, dy) )
        #                 except IndexError:
        #                     pass
        #         wall_item.draw(self.canvas)


        # rectangle = Clutter.Rectangle.new_with_color(colorMuddyBlue)
        # rectangle.set_size(200,50)
        # Clutter.Container.add_actor(window, rectangle)
        # # rectangle.show()
        # return rectangle
        pass

    def destroy(self):
        Clutter.main_quit()

    def onKeyPress(self, actor=None, event=None, data=None):
        """
        Basic key binding handler
        """
        print self, actor, event, data
        print dir(event)
        print event.keyval, event.modifier_state, repr(event.unicode_value)
        pressed = event.unicode_value

        # Evaluate the key modifiers
        state = event.modifier_state
        modShift = state & state.SHIFT_MASK == state.SHIFT_MASK
        modControl = state & state.CONTROL_MASK == state.CONTROL_MASK
        modMeta = state & state.META_MASK == state.META_MASK

        if pressed == 'q':
            print "Quitting"
            self.destroy()
        elif pressed == 'j':
            print "Down"
        elif pressed == 'k':
            print "Up"
        elif pressed == 'i':
            print "Interrupt - Debug"
            try:
                import ipdb as pdb
            except:
                import pdb
            pdb.set_trace()

def universe_for_testing():
    test_layout = (
    """ ##################
        # #.  .  # .     #
        # #####    ##### #
        #  0  . #  .  .#1#
        ################## """)
    universe = datamodel.create_CTFUniverse(test_layout, 2)
    return universe

################################################################################
# Main
################################################################################
def main():
    if DEBUG:
        Clutter.init(debugArgs)
    else:
        Clutter.init(sys.argv)

    universe = universe_for_testing()

    app = Canvas(universe)
    Clutter.main()
    
if __name__ == "__main__":
    sys.exit(main())

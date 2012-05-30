from __future__ import division
import sys
import glob
import random

from gi.repository import Clutter
from gi.repository import GObject
import cairo

from pelita.ui.clutter_tools import easing_state

from pelita import datamodel, layout

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
WALLS = glob.glob('/home/zbyszek/python/pelita/sprites/walls/*.png')

STEP_TIME = 0.25

moves_non_stop = datamodel.moves[:]
moves_non_stop.remove(datamodel.stop)

def _chain_of_neighbours(start, avail, orig):
    yield start
    moves = moves_non_stop[:]
    while True:
        for move in moves:
            candidate = (start[0] + move[0], start[1] + move[1])
            if candidate in avail:
                avail.pop(candidate)
                yield candidate
                start = candidate
                moves.sort(key=move.__ne__)
                break
        else:
            # try to join a different path if possible
            for move in moves:
                candidate = (start[0] + move[0], start[1] + move[1])
                if candidate in orig:
                    yield candidate
                    break
            return

def _maze_loner(avail, orig):
    for pool in orig, avail:
        for pos in avail:
            for move in moves_non_stop:
                candidate = (pos[0] + move[0], pos[1] + move[1])
                if candidate in pool:
                    break
            else:
                return pos
    keys = avail.keys()
    if not keys:
        raise StopIteration
    return avail.keys()[0]

def _maze_loners(avail, orig):
    while True:
        yield _maze_loner(avail, orig)

def iter_maze_by_walls(maze):
    cond = lambda items: datamodel.Wall in items
    avail = dict((pos, items) for (pos, items) in maze.iteritems()
                 if cond(items))
    orig = avail.copy()
    prev_path = None
    for start in _maze_loners(avail, orig):
        # start from the same one as long as possible
        avail.pop(start)
        while True:
            one_path = list(_chain_of_neighbours(start, avail, orig))
            if one_path == prev_path:
                break # next starting position
            yield one_path
            prev_path = one_path

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


class Canvas(object):
    pixels_per_cell = 60

    def __init__(self, geometry=None):
        "Nothing to do until we have the universe"
        self.geometry = geometry

    def create(self, universe):
        self.universe = universe

        stage = Clutter.Stage.get_default()
        stage.set_color(colorBlack)
        stage.set_title("Pelita")
        width, height = universe.maze.width, universe.maze.height
        # TODO: look at self.geometry
        stage.set_size(*self._pos_to_coord((width, height)))
        stage.set_reactive(True)

        print universe.pretty

        # Create a rectangle
        self.create_maze(stage, universe)

        self.create_bots(stage, universe)

        # Setup some key bindings on the main stage
        stage.connect_after("key-press-event", self.onKeyPress)

        # Present the main stage (and make sure everything is shown)
        stage.show_all()

    def _pos_to_coord(self, col_row):
        ans = (self.pixels_per_cell * col_row[0],
               self.pixels_per_cell * col_row[1])
        return ans

    def _create_bot(self, window, bot):
        filename = random.choice(BADDIES)
        print 'bot', bot, 'from', filename
        t = Clutter.Texture(filename=filename)
        width, height = t.get_size()
        if width == 0 or height == 0:
            raise ValueError("failed to load image: '%s'" % filename)
        t.set_size(self.pixels_per_cell, self.pixels_per_cell)
        t.set_position(*self._pos_to_coord(bot.current_pos))
        window.add_actor(t)
        return t

    def create_bots(self, window, universe):
        self._bot_actors = [self._create_bot(window, bot)
                            for bot in universe.bots]

    def _move_bots_random(self):
        for bot in self.universe.bots:
            legal_moves = self.universe.get_legal_moves(bot.current_pos).keys()
            move = random.choice(legal_moves)
            self.universe.move_bot(bot.index, move)
            self.move_bot(bot)
        return True

    def move_bot(self, bot):
        actor = self._bot_actors[bot.index]
        with easing_state(actor, duration=STEP_TIME*1000,
                          mode=Clutter.AnimationMode.EASE_IN_QUAD):
            actor.set_position(*self._pos_to_coord(bot.current_pos))

    def create_maze(self, window, universe):
        w, h = window.get_size()
        maze = MazeTexture(universe.maze, osd=self.osd,
                           width=w, height=h, auto_resize=True)
        window.add_actor(maze)
        return maze

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

        global STEP_TIME
        if pressed == 'q':
            print "Quitting"
            self.destroy()
        elif pressed == '-':
            STEP_TIME *= 3/4
            self.osd('STEP_TIME = %f s' % STEP_TIME)
        elif pressed == '=':
            STEP_TIME *= 4/3
            self.osd('STEP_TIME = %f s' % STEP_TIME)
        elif pressed == 'i':
            print "Interrupt - Debug"
            try:
                import ipdb as pdb
            except:
                import pdb
            pdb.set_trace()

    def osd(self, message):
        # TODO: implement osd
        print 'osd: ', message

class MazeTexture(Clutter.CairoTexture):
    def __init__(self, maze, osd, **kwargs):
        super(MazeTexture, self).__init__(**kwargs)
        self.maze = maze

        filename = random.choice(WALLS)
        osd("using '%s' for wall" % filename)
        ims = cairo.ImageSurface.create_from_png(filename)
        self.wall_pattern = cairo.SurfacePattern(ims)

        self.connect('draw', self._on_draw)
        self.invalidate() # XXX: necessary?
        print maze

    def _on_draw(self, texture, cr):
        # Scale to surface size
        width_, height_ = self.get_surface_size()
        width, height = self.maze.width, self.maze.height
        cr.scale(width_ / width, height_ / height)

        # Clear our surface
        cr.set_operator (cairo.OPERATOR_CLEAR)
        cr.paint()

        cr.set_operator(cairo.OPERATOR_OVER)

        # who doesn't want all those nice line settings :)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_width(0.3)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)

        # translate to the center of the top-left cell
        cr.translate(0.5, 0.5)
        # cr.set_source_rgba(0, 150, 0, 1)
        cr.set_source(self.wall_pattern)
        self._draw_walls(cr)

    def _draw_walls(self, cr):
        for list_of_pos in iter_maze_by_walls(self.maze):
            cr.move_to(*list_of_pos[0])
            for pos in list_of_pos[1:]:
                cr.line_to(*pos)
        # cr.rectangle(0, 0, width-1, height-1)
        cr.stroke()

def universe_for_testing():
    layout_str = layout.get_random_layout()
    nbots = layout.number_of_bots(layout_str)
    universe = datamodel.create_CTFUniverse(layout_str, nbots)
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

    app = Canvas()
    app.create(universe)
    GObject.timeout_add(int(STEP_TIME*1000), app._move_bots_random)

    Clutter.main()
    
if __name__ == "__main__":
    sys.exit(main())

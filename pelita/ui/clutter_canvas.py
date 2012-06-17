from __future__ import division
import os
import sys
import glob
import random

from gi.repository import Clutter
from gi.repository import GObject
import cairo

from .clutter_tools import easing_state, clutter_texture

from pelita import datamodel, layout


# An easy way to debug clutter and cogl without having to type the
# command line arguments
#DEBUG = True
DEBUG = False
debugArgs = ['--clutter-debug=all', '--cogl-debug=all']

# Define some standard colors to make basic color assigments easier
colorWhite = Clutter.Color.new(255,205,255,200)
colorMuddyBlue = Clutter.Color.new(49,78,108,255)
colorBlack = Clutter.Color.new(0,0,0,255)
colorGreenish = Clutter.Color.new(0,100,0,100)
colorBlueish = Clutter.Color.new(0,0,100,200)

_sprite_base = os.path.join(os.path.dirname(__file__), '..', '..', 'sprites')
BADDIES = glob.glob(os.path.join(_sprite_base, 'baddies', '*.svg'))
FOOD = glob.glob(os.path.join(_sprite_base, 'food', '*.svg'))
WALLS = glob.glob(os.path.join(_sprite_base, 'walls', '*.png'))

STEP_TIME = 0.25

moves_non_stop = datamodel.moves[:]
moves_non_stop.remove(datamodel.stop)

def _chain_of_neighbours(start, avail, orig):
    yield start
    moves = moves_non_stop[:]
    prev = None
    while True:
        for move in moves:
            candidate = (start[0] + move[0], start[1] + move[1])
            if candidate in avail:
                avail.pop(candidate)
                yield candidate
                prev, start = start, candidate
                moves.sort(key=move.__ne__)
                break
        else:
            # try to join a different path if possible
            for move in moves:
                candidate = (start[0] + move[0], start[1] + move[1])
                if candidate in orig and candidate != prev:
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


class Canvas(object):
    def __init__(self, step_time=STEP_TIME, geometry=None):
        "Nothing to do until we have the universe"
        print 'geometry', geometry
        self.geometry = geometry or (900, 510)
        self.step_time = step_time
        self.paused = False
        self.unpauser = None

    def create(self, universe):
        self.universe = universe
        width, height = universe.maze.width, universe.maze.height

        self.set_pixels_per_cell(self.geometry, universe)

        stage = Clutter.Stage.get_default()
        stage.set_color(colorBlack)
        stage.set_title("Pelita")
        stage.set_user_resizable(True)
        stage.set_size(*self._pos_to_coord((width, height+2)))
        stage.set_reactive(True)

        print universe.pretty

        # Create a main layout manager
        layoutManager = Clutter.BoxLayout()
        layoutManager.set_vertical(True)
        layoutManager.set_homogeneous(False)
        layoutManager.set_pack_start(False)

        stage.set_layout_manager(layoutManager)

        self.create_score(stage, universe)

        fixedlayout = Clutter.FixedLayout.new()
        container = Clutter.Box.new(fixedlayout)
        container.set_color(colorGreenish)
        stage.add_actor(container)

        self.mainWindow = container
        self.mainManager = fixedlayout

        self.create_maze(container, fixedlayout, universe)
        self.create_foods(container, universe)
        self.create_bots(container, universe)

        # Setup some key bindings on the main stage
        stage.connect_after('key-press-event', self.on_key_press)
        stage.connect_after('allocation-changed', self.on_allocation_changed, universe)

        # Present the main stage (and make sure everything is shown)
        stage.show_all()

    def set_pixels_per_cell(self, geometry, universe):
        geom_width, geom_height = geometry
        width, height = universe.maze.width, universe.maze.height
        self.pixels_per_cell = min(geom_width / width, geom_height / height)

    def _pos_to_coord(self, col_row, offset=(0,0)):
        ans = (self.pixels_per_cell * (col_row[0] + offset[0]),
               self.pixels_per_cell * (col_row[1] + offset[1]))
        return ans

    def update_score(self, universe):
        assert len(universe.teams) == 2

        teamname1 = universe.teams[0].name
        teamname2 = universe.teams[1].name
        score1 = universe.teams[0].score
        score2 = universe.teams[1].score

        msg = '%s %d:%d %s' % (teamname1, score1, score2, teamname2)
        self.score_text.set_text(msg)

    def create_score(self, window, universe):
        txtFont = "Mono 20"
        self.score_text = Clutter.Text.new_full(txtFont, '', colorWhite)
        self.update_score(universe)
        window.add_actor(self.score_text)

    def _create_bot(self, window, bot):
        filename = random.choice(BADDIES)
        print 'bot', bot, 'from', filename
        t = clutter_texture(filename, name='Bot-%d'%bot.index)
        t.set_size(self.pixels_per_cell, self.pixels_per_cell)
        t.set_position(*self._pos_to_coord(bot.current_pos))
        window.add_actor(t)
        return t

    def _create_food_model(self):
        filename = random.choice(FOOD)
        print 'food from', filename
        t = clutter_texture(filename, name='food')
        t.set_size(self.pixels_per_cell/2, self.pixels_per_cell/2)
        return t

    def _create_food(self, window, pos):
        if self._food_model is None:
            t = self._food_model = self._create_food_model()
        else:
            t = Clutter.Clone(source=self._food_model)
        pos = self._pos_to_coord(pos, offset=(0.25, 0.25))
        t.set_position(*pos)
        window.add_actor(t)
        #print 'food', pos, 'from', filename
        return t

    def create_foods(self, window, universe):
        self._food_model = None
        self._food = {pos:self._create_food(window, pos)
                      for pos in universe.maze.pos_of(datamodel.Food)}

    def eat_food(self, food_pos):
        self._food[food_pos].hide()

    def create_bots(self, window, universe):
        self._bot_actors = [self._create_bot(window, bot)
                            for bot in universe.bots]

    def create_random_movement(self):
        self._callback_time = self.step_time
        GObject.timeout_add(int(self._callback_time*1000),
                            self._move_bots_random)

    def _move_bots_random(self):
        for bot in self.universe.bots:
            legal_moves = self.universe.get_legal_moves(bot.current_pos).keys()
            move = random.choice(legal_moves)
            self.universe.move_bot(bot.index, move)
            self.move_bot(bot.index, move)
        if self.step_time != self._callback_time:
            self.create_random_movement()
            return False # kill this callback
        return True

    def move_bot(self, bot_index, pos):
        actor = self._bot_actors[bot_index]
        with easing_state(actor, duration=self.step_time*1000,
                          mode=Clutter.AnimationMode.EASE_IN_QUAD):
            actor.set_position(*self._pos_to_coord(pos))

    def create_maze(self, window, manager, universe):
        w, h = self._pos_to_coord((universe.maze.width, universe.maze.height))
        print 'adding maze with size', (w, h)
        maze = MazeTexture(universe.maze, osd=self.osd,
                           width=w, height=h, auto_resize=True,
                           coord_conv=self._pos_to_coord)
        window.add_actor(maze)
        # maze.set_background_color(colorGreenish)
        #manager.set_alignment(maze, Clutter.BoxAlignment.CENTER)
        #manager.set_expand(maze, True)
        self.maze = maze
        return maze

    def destroy(self):
        Clutter.main_quit()

    def on_key_press(self, actor=None, event=None, data=None):
        """
        Basic key binding handler
        """
        print 'on_key_press', self, actor, event, data
        print 'key', event.keyval, event.modifier_state, repr(event.unicode_value)
        pressed = event.unicode_value

        # Evaluate the key modifiers
        state = event.modifier_state
        modShift = state & state.SHIFT_MASK == state.SHIFT_MASK
        modControl = state & state.CONTROL_MASK == state.CONTROL_MASK
        modMeta = state & state.META_MASK == state.META_MASK

        if pressed == 'q':
            print "Quitting"
            self.destroy()
        elif pressed == '=':
            self.step_time *= 3/4
            self.osd('step_time = %f s' % self.step_time)
        elif pressed == '-':
            self.step_time *= 4/3
            self.osd('step_time = %f s' % self.step_time)
        elif pressed == ' ':
            self.paused ^= 1
            if not self.paused and self.unpauser:
                self.unpauser()
            self.osd('pause/play')
        elif pressed == 'i':
            print "Interrupt - Debug"
            try:
                import ipdb as pdb
            except:
                import pdb
            pdb.set_trace()

    def on_allocation_changed(self, stage, box, flags, universe):
        print 'allocation_changed', stage, box, flags
        width, height = self.universe.maze.width, self.universe.maze.height

        self.set_pixels_per_cell(stage.get_size(), universe)

        self.maze.set_size(*self._pos_to_coord((width, height)))

        for pos,t in self._food.iteritems():
            pos = self._pos_to_coord(pos, offset=(0.25, 0.25))
            t.set_position(*pos)

        # self.score_resize(stage)

    def osd(self, message):
        # TODO: implement osd
        print 'osd: ', message

class MazeTexture(Clutter.CairoTexture):
    def __init__(self, maze, osd, coord_conv, **kwargs):
        super(MazeTexture, self).__init__(name=self.__class__.__name__,
                                          **kwargs)
        self.maze = maze
        self.osd = osd

        self.create_wall_pattern()
        self.coord_conv = coord_conv

        self.connect('draw', self._on_draw)
        self.invalidate() # XXX: necessary?
        print 'maze is ready'

    def create_wall_pattern(self):
        try:
            filename = random.choice(WALLS)
            ims = cairo.ImageSurface.create_from_png(filename)
            pattern = cairo.SurfacePattern(ims)
            pattern.set_extend(True)
            self.osd("using '%s' for wall" % filename)
        except Exception as e:
            self.osd("exception: %s" % e)
            pattern = cairo.SolidPattern(0, 150, 0, 1)
            self.osd("using solid color for wall")
        self.wall_pattern = pattern

    def _on_draw(self, texture, cr):
        # Scale to surface size
        width_, height_ = self.get_surface_size()
        print 'redraw', (width_, height_)

        # cr.scale(1.0, 1.0)

        # Clear our surface
        cr.set_operator (cairo.OPERATOR_CLEAR)
        cr.paint()

        cr.set_operator(cairo.OPERATOR_OVER)

        # who doesn't want all those nice line settings :)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_width(10)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)

        # cr.set_source_rgba(0, 150, 0, 1)
        cr.set_source(self.wall_pattern)
        self._draw_walls(cr)

    def _draw_walls(self, cr):
        for list_of_pos in iter_maze_by_walls(self.maze):
            assert len(list_of_pos) >= 1
            coord = self.coord_conv(list_of_pos[0], offset=(0.5, 0.5))
            cr.move_to(*coord)
            for pos in list_of_pos:
                cr.line_to(*self.coord_conv(pos, offset=(0.5, 0.5)))
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
    app.create_random_movement()

    Clutter.main()

if __name__ == "__main__":
    sys.exit(main())

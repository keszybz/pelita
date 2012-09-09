# -*- coding: utf-8 -*-

""" The datamodel. """

import copy
from .layout import Layout
from .containers import Mesh
from .messaging.json_convert import serializable


__docformat__ = "restructuredtext"

north = (0, -1)
south = (0, 1)
west  = (-1, 0)
east  = (1, 0)
stop  = (0, 0)

moves = [north, south, east, west, stop]

# the number of points to score when killing
KILLPOINTS=5

def new_pos(position, move):
    """ Adds a position tuple and a move tuple.

    Parameters
    ----------
    position : tuple of int (x, y)
        current position

    move : tuple of int (x, y)
        direction vector

    Returns
    -------
    new_pos : tuple of int (x, y)
        new position coordinates

    Raises
    ------
    ValueError
        if move is not one of the 5 possible moves
        (`north`, `south`, `east`, `west` or `stop`)

    """
    if move not in moves:
        raise ValueError("%s is not a valid move tuple" % repr(move))
    pos_x = position[0] + move[0]
    pos_y = position[1] + move[1]
    return (pos_x, pos_y)

def diff_pos(initial, target):
    """ Return the move required to move from one position to another.

    Will return the move required to transition from `initial` to `target`. If
    `initial` equals `target` this is `stop`. If the two are not adjacent a
    `ValueError` will be raised.

    Parameters
    ----------
    initial : tuple of (int, int)
        the starting position
    target : tuple of (int, int)
        the target position

    Returns
    -------
    move : tuple of (int, int)
        the resulting move

    Raises
    ------
    ValueError
        if `initial` is not adjacent to `target`

    """
    if initial == target:
        return stop
    elif not is_adjacent(initial, target):
        raise ValueError('%r is not adjacent to %r' % (initial, target))
    else:
        return (target[0]-initial[0], target[1]-initial[1])

def is_adjacent(pos1, pos2):
    """ Check that two positions are adjacent.

    This will check that the Manhattan distance between two positions is exactly
    one. This function does not take into account if the resulting position is a
    legal position in a Maze.

    Parameters
    ----------
    pos1 : tuple of (int, int)
        the first position
    pos2 : tuple of (int, int)
        the second position

    Returns
    -------
    is_adjacent : boolean
        True if pos1 is adjacent to pos2 and False otherwise

    """
    return (pos1[0] == pos2[0] and abs(pos1[1] - pos2[1]) == 1 or
        pos1[1] == pos2[1] and abs(pos1[0] - pos2[0]) == 1)

def manhattan_dist(pos1, pos2):
    """ Manhattan distance between two points.

    Parameters
    ----------
    pos1 : tuple of (int, int)
        the first position
    pos2 : tuple of (int, int)
        the second position

    Returns
    -------
    manhattan_dist : int
        Manhattan distance between two points
    """
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

@serializable
class Team(object):
    """ A team of bots.

    Parameters
    ----------
    index : int
        the index of the team within the Universe
    name : str
        the name of the team
    zone : tuple of int (x_min, x_max)
        the homezone of this team
    score : int, optional, default = 0
        the score of this team
    bots : list of int, optional, default = None (creates an empty list)
        the bot indices that belong to this team

    """
    def __init__(self, index, name, zone, score=0, bots=None):
        self.index = index
        self.name = name
        self.zone = zone
        self.score = score
        # we can't use a keyword argument here, because that would create a
        # single list object for all our Teams.
        if bots is None:
            self.bots = []
        else:
            self.bots = bots

    def _add_bot(self, bot):
        """ Add a bot to this team.

        Parameters
        ----------
        bot : int
            the index of the bot to add

        """
        self.bots.append(bot)

    def in_zone(self, position):
        """ Check if a position is within the zone of this team.

        Parameters
        ----------
        position : tuple of int (x, y)
            the position to check

        Returns
        -------
        is_in_zone : boolean
            True if the position is in the homezone and False otherwise

        """
        return self.zone[0] <= position[0] <= self.zone[1]

    def _score_point(self):
        """ Score a single point. """
        self.score += 1

    def _score_points(self, points):
        """ Score several points. """
        self.score += points

    def __str__(self):
        return self.name

    def __repr__(self):
        return ('Team(%i, %r, %s, score=%i, bots=%r)' %
                (self.index, self.name, self.zone, self.score, self.bots))

    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)

    def _to_json_dict(self):
        return {"index": self.index,
                "name": self.name,
                "zone": self.zone,
                "score": self.score,
                "bots": self.bots}

    @classmethod
    def _from_json_dict(cls, item):
        # need to convert the json list to a tuple
        item["zone"] = tuple(item["zone"])
        return cls(**item)

@serializable
class Bot(object):
    """ A bot on a team.

    Parameters
    ----------
    index : int
        the index of this bot within the Universe
    initial_pos : tuple of int (x, y)
        the initial position for this bot
    team_index : int
        the index of the team that this bot is on
    homezone : tuple of int (x_min, x_max)
        the homezone of this team
    current_pos : tuple of int (x, y), optional
        the current position of this bot
        default = None (will be set to initial_pos)

    Attributes
    ----------
    in_own_zone : boolean, property
        True if in its own homezone and False otherwise
    is_destroyer : boolean, property
        True if a destroyer, False otherwise
    is_harvester : boolean, property
        not is_destroyer
    noisy : boolean
        True if the position is noisy, False if it is exact

    """
    def __init__(self, index, initial_pos, team_index, homezone,
            current_pos=None, noisy=False):
        self.index = index
        self.initial_pos = initial_pos
        self.team_index = team_index
        self.homezone = homezone
        if not current_pos:
            self.current_pos = self.initial_pos
        else:
            self.current_pos = current_pos
        self.noisy = noisy

    @property
    def in_own_zone(self):
        return self.homezone[0] <= self.current_pos[0] <= self.homezone[1]

    @property
    def is_destroyer(self):
        return self.in_own_zone

    @property
    def is_harvester(self):
        return not self.is_destroyer

    def _reset(self):
        """ Reset this bot to its initial position. """
        self.current_pos = self.initial_pos

    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)

    def __cmp__(self, other):
        if self == other:
            return 0
        else:
            return self.index.__cmp__(other.index)

    def __repr__(self):
        return ('Bot(%i, %s, %i, %s , current_pos=%s, noisy=%r)' %
                (self.index, self.initial_pos, self.team_index,
                    self.homezone, self.current_pos, self.noisy))

    def _to_json_dict(self):
        return {"index": self.index,
                "initial_pos": self.initial_pos,
                "team_index": self.team_index,
                "homezone": self.homezone,
                "current_pos": self.current_pos,
                "noisy": self.noisy}

    @classmethod
    def _from_json_dict(cls, item):
        # need to convert the json list to a tuple
        for tupled_attr in ["initial_pos", "homezone", "current_pos"]:
            item[tupled_attr] = tuple(item[tupled_attr])
        return cls(**item)

Free = ' '
Wall = '#'
Food = '.'

maze_components = [Food, Free, Wall]

@serializable
class Maze(Mesh):
    """ A Mesh of strings of maze component representations.

    This is a container class to represent a game maze. It is a two-dimensional
    structure (Mesh) which contains a representation of maze components at each
    position. This is implemented using sequences of characters, i.e. strings.
    At each position we store the characters corresponding to the maze
    components at this position.
    """

    def __init__(self, width, height, data=None):
        if not data:
            data = ["" for i in range(width*height)]
        elif not all(isinstance(s, str) for s in data):
            raise TypeError("Maze keyword argument 'data' should be list of " +\
                            "strings, not: %r" % data)
        else:
            # sort the data items
            data = ["".join(sorted(v)) for v in data]
        super(Maze, self).__init__(width, height, data)

    def __setitem__(self, key, value):
        super(Maze, self).__setitem__(key, "".join(sorted(value)))

    def get_at(self, char, pos):
        """ Get all objects of a given char representation at certain position.

        Parameters
        ----------
        char : char
            the char representation of maze components to look for
        pos : tuple of (int, int)
            the position to look at

        Returns
        -------
        objs : list
            the objects at that position

        """
        return [item for item in self[pos] if item == char]

    def remove_at(self, char, pos):
        """ Remove all objects of a given char representation at a certain position.

        Parameters
        ----------
        char : char
            the char representation to remove from the Maze
        pos : tuple of (int, int)
            the position to look at

        """
        if char in self[pos]:
            self[pos] = [item for item in self[pos] if item != char]
        else:
            raise ValueError

    @property
    def positions(self):
        """ The indices of positions in the Maze.

        Returns
        -------
        positions : list of tuple of (int, int)
            the positions (x, y) in the Maze

        """
        return list(self.keys())

    def pos_of(self, char):
        """ The indices of positions which have a maze component.

        Parameters
        ----------
        char : maze component char
            the char of maze component to look for

        Examples
        --------
        >>> universe.maze.pos_of(Free)
        [(1, 1),
        (3, 1),
        (4, 1),
        (5, 1),
        (6, 1),
        (7, 1),
        ...

        """
        return [pos for pos, val in self.items() if char in val]

    def __repr__(self):
        return ('Maze(%i, %i, data=%r)'
            % (self.width, self.height, self._data))


def create_maze(layout_mesh):
    """ Transforms a layout_mesh into a Maze.

    Parameters
    ----------
    layout_mesh : Mesh of single char strings
        Mesh of single character strings describing the layout

    Returns
    -------
    maze : Maze
        the Maze

    """
    maze = Maze(layout_mesh.width, layout_mesh.height)
    for index in maze.keys():
        if layout_mesh[index] == Wall:
            maze[index] = maze[index] + Wall
        else:
            maze[index] = maze[index] + Free
        if layout_mesh[index] == Food:
            maze[index] = maze[index] + Food
    return maze


def extract_initial_positions(mesh, number_bots):
    """ Extract initial positions from mesh.

    Also replaces the initial positions in the mesh with free spaces.

    Parameters
    ----------
    mesh : Mesh of characters
        the layout in mesh format
    number_bots : int
        the number of bots for which to find initial positions

    Returns
    -------
    initial pos : list of tuples
        the initial positions for all the bots
    """
    bot_ids = [str(i) for i in range(number_bots)]
    start = [(0, 0)] * number_bots
    for k, v in mesh.items():
        if v in bot_ids:
            start[int(v)] = k
            mesh[k] = Free
    return start


def create_CTFUniverse(layout_str, number_bots,
        team_names=None):
    """ Factory to create a 2-Player Capture The Flag Universe.

    Parameters
    ----------
    layout_str : str
        the string encoding the maze layout
    number_bots : int
        the number of bots in the game
    team_names : length 2 list of strings, optional
        default = None -> ['black', 'white']
        the names of the playing teams

    Raises
    ------
    UniverseException
        if the number of bots or layout width are odd
    LayoutEncodingException
        if there is something wrong with the layout_str, see `Layout()`

    """
    if team_names is None:
        team_names = ["black", "white"]

    layout_chars = maze_components

    if number_bots % 2 != 0:
        raise UniverseException(
            "Number of bots in CTF must be even, is: %i"
            % number_bots)
    layout = Layout(layout_str, layout_chars, number_bots)
    layout_mesh = layout.as_mesh()
    initial_pos = extract_initial_positions(layout_mesh, number_bots)
    maze = create_maze(layout_mesh)
    if maze.width % 2 != 0:
        raise UniverseException(
            "Width of a layout for CTF must be even, is: %i"
            % maze.width)
    homezones = [(0, maze.width // 2 - 1),
            (maze.width // 2, maze.width - 1)]

    teams = []
    teams.append(Team(0, team_names[0], homezones[0], bots=list(range(0,
        number_bots, 2))))
    teams.append(Team(1, team_names[1], homezones[1], bots=list(range(1,
        number_bots, 2))))

    bots = []
    for bot_index in range(number_bots):
        team_index = bot_index % 2
        bot = Bot(bot_index, initial_pos[bot_index],
                team_index, homezones[team_index])
        bots.append(bot)

    return CTFUniverse(maze, teams, bots)


class UniverseException(Exception):
    """ Standard error in the Universe. """
    pass


class IllegalMoveException(Exception):
    """ Raised when a bot attempts to make an illegal move. """
    pass

@serializable
class CTFUniverse(object):
    """ The Universe: representation of the game state.

    Parameters
    ----------
    maze : Maze object
        the maze
    teams : list of Team objects
        the teams
    bots : list of Bot objects
        the bots

    Attributes
    ----------
    bot_positions : list of tuple of ints (x, y), property
        the current position of all bots
    food_list : list of tuple of ints (x, y), property
        the positions of all edible food

    """


    def __init__(self, maze, teams, bots):
        self.maze = maze
        # TODO make a deepcopy here, so that we can big_bang
        self.teams = teams
        self.bots = bots

    @property
    def bot_positions(self):
        """ Current positions of all bots.

        Returns
        -------
        bot_positions : list of tuple of (int, int)
            the positions of all bots
        """
        return [bot.current_pos for bot in self.bots]

    @property
    def food_list(self):
        """ Positions of all the food.

        Returns
        -------
        food_positions : list of tuple of (int, int)
            the positions of all food

        """
        return self.maze.pos_of(Food)

    def team_food(self, team_index):
        """ Food that is owned by a team

        Returns
        -------
        team_food : list of tuple of (int, int)
            food owned by team

        """
        return [pos for pos in self.food_list
                if self.teams[team_index].in_zone(pos)]

    def enemy_food(self, team_index):
        """ Food that is edible by a team

        Returns
        -------
        team_food : list of tuple of (int, int)
            food edible by team

        """
        return [pos for pos in self.food_list
                if not self.teams[team_index].in_zone(pos)]

    def other_team_bots(self, bot_index):
        """ Obtain other bots on team.

        Parameters
        ----------
        bot_index : int
            index of the bot in question

        Returns
        -------
        other_team_bots : list of Bot objects
            the other bots on the team, excluding the desired bot

        """
        team = self.teams[self.bots[bot_index].team_index]
        return [self.bots[i] for i in team.bots if i != bot_index]

    def team_bots(self, team_index):
        """ Obtain all Bot objects in a Team.

        Parameters
        ----------
        team_index : int
            the index of the desired team

        Returns
        -------
        team_bots : list of Bot objects

        """
        return [self.bots[i] for i in self.teams[team_index].bots]

    def enemy_bots(self, team_index):
        """ Obtain enemy bot objects.

        Parameters
        ----------
        team_index : int
            the index of the 'friendly' team

        Returns
        -------
        enemy_bots : list of Bot objects

        """
        return [self.bots[i] for i in self.enemy_team(team_index).bots]

    def enemy_team(self, team_index):
        """ Obtain the enemy team.

        Parameters
        ----------
        team_index : int
            the index of the 'friendly' team

        Returns
        -------
        enemy_team : Team object

        Raises
        ------
        UniverseException
            if there is more than one enemy team
        """
        other_teams = self.teams[:]
        other_teams.remove(self.teams[team_index])
        if len(other_teams) != 1:
            raise UniverseException("Expecting one enemy team. Found %i." % len(other_teams))
        return other_teams[0]

    def team_border(self, team_index):
        """ Positions of the border positions.

        These are the last positions in the zone of the team.

        Parameters
        ----------
        team_index : int
            the index of the 'friendly' team

        Returns
        -------
        team_border : list of tuple of (int, int)
            the border positions

        """
        x_min, x_max = 0, self.maze.shape[0]
        team_zone = self.teams[team_index].zone
        if team_zone[0] == x_min:
            border_x = team_zone[1]
        else:
            border_x = team_zone[0]
        return [(border_x, y) for y in range(self.maze.shape[1]) if
                Free in self.maze[border_x, y]]

    def move_bot(self, bot_id, move):
        """ Move a bot in certain direction.

        Parameters
        ----------
        bot_id : int
            index of the bot
        move : tuple of (int, int)
            direction to move in

        Returns
        -------
        game_state : dict
            the current game_state

        Raises
        ------
        IllegalMoveException
            if the move is invalid or impossible

        """
        # check legality of the move

        game_state = {}

        bot = self.bots[bot_id]
        legal_moves_dict = self.get_legal_moves(bot.current_pos)
        if move not in list(legal_moves_dict.keys()):
            raise IllegalMoveException(
                'Illegal move from bot_id %r: %s' % (bot_id, move))
        old_pos = bot.current_pos
        new_pos = bot.current_pos = legal_moves_dict[move]

        game_state["bot_moved"] = [{"bot_id": bot_id, "old_pos": old_pos, "new_pos": new_pos}]

        team = self.teams[bot.team_index]
        # check for food being eaten
        game_state["food_eaten"] = []
        if Food in self.maze[bot.current_pos] and not bot.in_own_zone:
            self.maze.remove_at(Food, bot.current_pos)

            game_state["food_eaten"] += [{"food_pos": bot.current_pos, "bot_id": bot_id}]

        # check for destruction
        game_state["bot_destroyed"] = []
        for enemy in self.enemy_bots(bot.team_index):
            if enemy.current_pos == bot.current_pos:
                if enemy.is_destroyer and bot.is_harvester:
                    game_state["bot_destroyed"] += [{'bot_id': bot.index, 'destroyed_by': enemy.index}]
                elif enemy.is_harvester and bot.is_destroyer:
                    game_state["bot_destroyed"] += [{'bot_id': enemy.index, 'destroyed_by': bot.index}]

        # reset bots
        for destroyed in game_state["bot_destroyed"]:
            old_pos = bot.current_pos
            self.bots[destroyed["bot_id"]]._reset()
            new_pos = bot.current_pos
            game_state["bot_moved"] += [{"bot_id": bot_id, "old_pos": old_pos, "new_pos": new_pos}]

        for food_eaten in game_state["food_eaten"]:
            self.teams[self.bots[food_eaten["bot_id"]].team_index].score += 1

        for bot_destroyed in game_state["bot_destroyed"]:
            self.teams[self.bots[bot_destroyed["destroyed_by"]].team_index].score += KILLPOINTS

        return game_state

        # TODO:
        # check for state change

    def get_legal_moves(self, position):
        """ Obtain legal moves and where they lead.

        Parameters
        ----------
        position : tuple of int (x, y)
            the position to start at

        Returns
        -------
        legal_moves_dict : dict mapping strings (moves) to positions (x, y)
            the legal moves and where they would lead.

        """
        legal_moves_dict = {}
        for move, new_pos in list(self.neighbourhood(position).items()):
            if Free in self.maze[new_pos]:
                legal_moves_dict[move] = new_pos
        return legal_moves_dict

    def get_legal_moves_or_stop(self, position):
        """ Obtain legal moves (and where they lead)
        or just stop if impossible to move.

        Parameters
        ----------
        position : tuple of int (x, y)
            the position to start at

        Returns
        -------
        legal_moves : dict mapping strings (moves) to positions (x, y)
            the legal moves and where they would lead.
        """
        moves = self.get_legal_moves(position)

        if len(moves) > 1:
            del moves[stop]
        return moves

    def __repr__(self):
        return ("CTFUniverse(%r, %r, %r)" %
            (self.maze, self.teams, self.bots))

    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)

    @property
    def _char_mesh(self):
        char_mesh = Mesh(self.maze.width, self.maze.height)
        for pos in self.maze.positions:
                if Wall in self.maze[pos]:
                    char_mesh[pos] = Wall
                elif Food in self.maze[pos]:
                    char_mesh[pos] = Food
                elif Free in self.maze[pos]:
                    char_mesh[pos] = Free
        for bot in self.bots:
            # TODO what about bots on the same space?
            char_mesh[bot.current_pos] = str(bot.index)
        return char_mesh

    def __str__(self):
        return str(self._char_mesh)

    def copy(self):
        return copy.deepcopy(self)

    @property
    def compact_str(self):
        return self._char_mesh.compact_str

    @property
    def pretty(self):
        """ Provide detailed, readable info about universe state.

        Returns
        -------
        pretty : str
            detailed, readable string version of this universe

        Examples
        --------
        >>> universe.pretty
        ##################
        #0#.  .  # .     #
        #1#####    #####2#
        #     . #  .  .#3#
        ##################
        Team(0, 'black', (0, 8), score=0, bots=[0, 2])
            Bot(0, (1, 1), 0, (0, 8) , current_pos=(1, 1))
            Bot(2, (16, 2), 0, (0, 8) , current_pos=(16, 2))
        Team(1, 'white', (9, 17), score=0, bots=[1, 3])
            Bot(1, (1, 2), 1, (9, 17) , current_pos=(1, 2))
            Bot(3, (16, 3), 1, (9, 17) , current_pos=(16, 3))

        """
        out = str()
        out += self.compact_str
        for team in self.teams:
            out += repr(team)
            out += '\n'
            for i in team.bots:
                out += '\t' + repr(self.bots[i])
                out += '\n'
        return out

    def neighbourhood(self, position):
        """ Determine where a move will lead.

        Parameters
        ----------
        position : tuple of int (x, y)
            current position

        Returns
        -------
        new_pos : dict
            mapping of moves to new positions (x, y)

        """
        return dict([(move, new_pos(position, move)) for move in moves])

    def _to_json_dict(self):
        return {"maze": self.maze,
                "teams": self.teams,
                "bots": self.bots}

    @classmethod
    def _from_json_dict(cls, item):
        return cls(**item)


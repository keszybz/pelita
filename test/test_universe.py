import unittest
from pelita.layout import Layout
from pelita.mesh import Mesh
from pelita.universe import *

class TestStaticmethods(unittest.TestCase):

    def test_get_initial_positions(self):

        layout_chars = [wall, food, harvester, destroyer, free]

        test_layout = (
            """ #######
                #0    #
                #  1  #
                #    2#
                ####### """)
        number_bots = 3
        layout = Layout(test_layout, layout_chars, number_bots)
        mesh = layout.as_mesh()
        initial_pos = extract_initial_positions(mesh, number_bots)
        target = [(1, 1), (3, 2), (5, 3)]
        self.assertEqual(target, initial_pos)
        # also test the side-effect of initial_positions()
        target = Mesh(7, 5, data =list('########     ##     ##     ########'))
        self.assertEqual(target, mesh)

        # now for a somewhat more realistic example
        test_layout2 = (
            """ ##################
                #0#      #       #
                #1#####    #####2#
                #       #      #3#
                ################## """)
        number_bots = 4
        layout = Layout(test_layout2, layout_chars, number_bots)
        mesh = layout.as_mesh()
        initial_pos = extract_initial_positions(mesh, number_bots)
        target = [(1, 1), (1, 2), (16, 2), (16, 3)]
        self.assertEqual(target, initial_pos)
        # also test the side-effect of initial_positions()
        target = Mesh(18, 5, data = list('################### #      #       #'+\
                '# #####    ##### ##       #      # ###################'))
        self.assertEqual(target, mesh)

    def test_new_positions(self):
        current_position = (1, 1)
        new = CTFUniverse.new_positions(current_position)
        target = { north : (1, 0),
                    south : (1, 2),
                    west  : (0, 1),
                    east  : (2, 1),
                    stop  : (1, 1) }
        self.assertEqual(target, new)

    def test_is_adjacent(self):
        self.assertTrue(CTFUniverse.is_adjacent((0, 0), (1, 0)))
        self.assertTrue(CTFUniverse.is_adjacent((0, 0), (0, 1)))
        self.assertFalse(CTFUniverse.is_adjacent((0, 0), (1, 1)))

        self.assertTrue(CTFUniverse.is_adjacent((1, 0), (0, 0)))
        self.assertTrue(CTFUniverse.is_adjacent((0, 1), (0, 0)))
        self.assertFalse(CTFUniverse.is_adjacent((1, 1), (0, 0)))

class TestBot(unittest.TestCase):

    def test_init_in_own_zone_is_harvester(self):
        bot = Bot(0, (1, 1), 0, (0, 3))
        self.assertEqual(bot.index, 0)
        self.assertEqual(bot.initial_pos, (1, 1))
        self.assertEqual(bot.current_pos, (1, 1))
        self.assertEqual(bot.team_index, 0)
        self.assertEqual(bot.homezone, (0, 3))
        self.assertTrue(bot.is_destroyer)
        self.assertFalse(bot.is_harvester)
        self.assertTrue(bot.in_own_zone)

        bot = Bot(1, (6, 6), 1, (3, 6), current_pos = (1, 1))
        self.assertEqual(bot.index, 1)
        self.assertEqual(bot.initial_pos, (6, 6))
        self.assertEqual(bot.current_pos, (1, 1))
        self.assertEqual(bot.team_index, 1)
        self.assertEqual(bot.homezone, (3, 6))
        self.assertFalse(bot.is_destroyer)
        self.assertTrue(bot.is_harvester)
        self.assertFalse(bot.in_own_zone)

    def test_eq_repr_cmp(self):
        black = Bot(0, (1, 1), 0, (0, 3))
        black2 = Bot(0, (1, 1), 0, (0, 3))
        white = Bot(1, (6, 6), 1, (3, 6), current_pos = (1, 1))
        self.assertNotEqual(black, white)
        self.assertEqual(black, black2)
        black3 = eval(black.__repr__())
        self.assertEqual(black, black3)
        self.assertEqual(black.__cmp__(black2), 0)
        self.assertEqual(black.__cmp__(white), -1)
        self.assertEqual(white.__cmp__(black),  1)

    def test_move_reset(self):
        black = Bot(0, (1, 1), 0, (0, 3))
        white = Bot(1, (6, 6), 1, (3, 6), current_pos = (1, 1))
        self.assertTrue(black.is_destroyer)
        black._move((4, 1))
        self.assertEqual(black.current_pos, (4, 1))
        self.assertTrue(black.is_harvester)
        self.assertTrue(white.is_harvester)
        black._reset()
        white._reset()
        self.assertEqual(black.current_pos, (1, 1))
        self.assertTrue(black.is_destroyer)
        self.assertEqual(white.current_pos, (6, 6))
        self.assertTrue(white.is_destroyer)

class TestTeam(unittest.TestCase):

    def test_init(self):
        team_black = Team(0, 'black', (0, 2))
        team_white = Team(1, 'white', (3, 6), score=5, bots=[1, 3, 5])

        self.assertEqual(team_black.index, 0)
        self.assertEqual(team_black.name, 'black')
        self.assertEqual(team_black.score, 0)
        self.assertEqual(team_black.zone, (0, 2))
        self.assertEqual(team_black.bots, [])

        self.assertEqual(team_white.index, 1)
        self.assertEqual(team_white.name, 'white')
        self.assertEqual(team_white.score, 5)
        self.assertEqual(team_white.zone, (3, 6))
        self.assertEqual(team_white.bots, [1, 3, 5])

    def test_methods(self):
        team_black = Team(0, 'black', (0, 2))
        team_white = Team(1, 'white', (3, 6), score=5, bots=[1, 3, 5])

        team_black._add_bot(0)
        self.assertEqual(team_black.bots, [0])
        team_white._add_bot(7)
        self.assertEqual(team_white.bots, [1, 3, 5, 7])
        self.assertTrue(team_black.in_zone((1, 5)))
        self.assertFalse(team_black.in_zone((5, 1)))
        self.assertTrue(team_white.in_zone((5, 1)))
        self.assertFalse(team_white.in_zone((1, 5)))
        team_black._score_point()
        self.assertEqual(team_black.score, 1)
        team_white._score_point()
        self.assertEqual(team_white.score, 6)

    def test_str_repr_eq(self):
        team_black = Team(0, 'black', (0, 2))
        team_white = Team(1, 'white', (3, 6), score=5, bots=[1, 3, 5])
        team_black2 = Team(0, 'black', (0, 2))
        self.assertEqual(team_black, team_black)
        self.assertEqual(team_black, team_black2)
        self.assertNotEqual(team_black, team_white)
        self.assertEqual(team_black.__str__(), 'black')
        self.assertEqual(team_white.__str__(), 'white')
        team_black3 = eval(team_black.__repr__())
        self.assertEqual(team_black, team_black3)
        team_white2 = eval(team_white.__repr__())
        self.assertEqual(team_white, team_white2)

class TestMazeComponents(unittest.TestCase):

    def test_init_str_eq_repr(self):
        wall = Wall()
        wall2 = Wall()
        free = Free()
        free2 = Free()
        food = Food()
        food2 = Food()
        self.assertEqual(wall, wall2)
        self.assertNotEqual(wall, free)
        self.assertNotEqual(wall, food)
        self.assertEqual(free, free2)
        self.assertNotEqual(free, wall)
        self.assertNotEqual(free, food)
        self.assertEqual(food, food2)
        self.assertNotEqual(food, wall)
        self.assertNotEqual(food, free)
        self.assertEqual(wall.__str__(), '#')
        self.assertEqual(free.__str__(), ' ')
        self.assertEqual(food.__str__(), '.')
        wall3 = eval(wall.__repr__())
        free3 = eval(free.__repr__())
        food3 = eval(food.__repr__())
        self.assertEqual(wall, wall3)
        self.assertEqual(free, free3)
        self.assertEqual(food, food3)

class TestCTFUniverse(unittest.TestCase):

    def test_factory(self):
        test_layout3 = (
        """ ##################
            #0#.  .  # .     #
            #1#####    #####2#
            #     . #  .  .#3#
            ################## """)
        universe = create_CTFUniverse(test_layout3, 4)
        # this checks that the methods extracts the food, and the initial
        # positions from the raw layout
        target_mesh = Mesh(18, 5, data = list('################### #.  .  # .     #'+\
                '# #####    ##### ##     . #  .  .# ###################'))
        target_mesh = create_maze(target_mesh)
        self.assertEqual(target_mesh, universe.maze_mesh)
        target_food_list = [(3, 1), (6, 1), (11, 1), (6, 3), (11, 3), (14, 3),  ]
        self.assertEqual(target_food_list, universe.food_list)

        self.assertEqual([b.initial_pos for b in universe.bots],
                [(1, 1), (1, 2), (16, 2), (16, 3)])

        odd_layout = (
            """ #####
                #0 1#
                ##### """)
        self.assertRaises(UniverseException, create_CTFUniverse, odd_layout, 2)

        odd_bots = (
            """ ####
                #01#
                #2 #
                #### """)
        self.assertRaises(UniverseException, create_CTFUniverse, odd_bots, 3)

        universe = create_CTFUniverse(test_layout3, 4, team_names=['orange', 'purple'])
        self.assertEqual(universe.teams[0].name, 'orange')
        self.assertEqual(universe.teams[1].name, 'purple')

    def test_bot_teams(self):

        test_layout4 = (
            """ ######
                #0  1#
                #2  3#
                ###### """)
        universe = create_CTFUniverse(test_layout4, 4)

        team_black = Team(0, 'black', (0, 2), bots=[0, 2])
        team_white = Team(1, 'white', (3, 5), bots=[1, 3])

        self.assertEqual(universe.teams[0], team_black)
        self.assertEqual(universe.teams[1], team_white)

        self.assertEqual(universe.bots[0].team_index, 0)
        self.assertEqual(universe.bots[2].team_index, 0)
        self.assertEqual(universe.bots[1].team_index, 1)
        self.assertEqual(universe.bots[3].team_index, 1)

        self.assertTrue(universe.bots[0].in_own_zone)
        self.assertTrue(universe.bots[1].in_own_zone)
        self.assertTrue(universe.bots[2].in_own_zone)
        self.assertTrue(universe.bots[3].in_own_zone)

        test_layout4 = (
            """ ######
                #1  0#
                #3  2#
                ###### """)
        universe = create_CTFUniverse(test_layout4, 4)

        self.assertFalse(universe.bots[0].in_own_zone)
        self.assertFalse(universe.bots[1].in_own_zone)
        self.assertFalse(universe.bots[2].in_own_zone)
        self.assertFalse(universe.bots[3].in_own_zone)

        test_layout4 = (
            """ ######
                #0 2 #
                # 1 3#
                ###### """)
        universe = create_CTFUniverse(test_layout4, 4)
        self.assertTrue(universe.bots[1].is_harvester)
        self.assertTrue(universe.bots[2].is_harvester)
        self.assertFalse(universe.bots[0].is_harvester)
        self.assertFalse(universe.bots[3].is_harvester)
        self.assertFalse(universe.bots[1].is_destroyer)
        self.assertFalse(universe.bots[2].is_destroyer)
        self.assertTrue(universe.bots[0].is_destroyer)
        self.assertTrue(universe.bots[3].is_destroyer)

class TestCTFUniverseRules(unittest.TestCase):

    def test_get_legal_moves(self):
        test_legal = (
            """ ######
                #  # #
                #   ##
                #    #
                ###### """)
        universe = create_CTFUniverse(test_legal, 0)
        legal_moves_1_1 = universe.get_legal_moves((1, 1))
        target = {east  : (2, 1),
                  south : (1, 2),
                  stop  : (1, 1)}
        self.assertEqual(target, legal_moves_1_1)
        legal_moves_2_1 = universe.get_legal_moves((2, 1))
        target = {west  : (1, 1),
                  south : (2, 2),
                  stop  : (2, 1)}
        self.assertEqual(target, legal_moves_2_1)
        legal_moves_4_1 = universe.get_legal_moves((4, 1))
        target = { stop : (4, 1)}
        self.assertEqual(target, legal_moves_4_1)
        legal_moves_1_2 = universe.get_legal_moves((1, 2))
        target = {north : (1, 1),
                  east  : (2, 2),
                  south : (1, 3),
                  stop  : (1, 2)}
        self.assertEqual(target, legal_moves_1_2)
        legal_moves_2_2 = universe.get_legal_moves((2, 2))
        target = {north : (2, 1),
                  east  : (3, 2),
                  south : (2, 3),
                  west  : (1, 2),
                  stop  : (2, 2)}
        self.assertEqual(target, legal_moves_2_2)
        legal_moves_3_2 = universe.get_legal_moves((3, 2))
        target = {south : (3, 3),
                  west  : (2, 2),
                  stop  : (3, 2)}
        self.assertEqual(target, legal_moves_3_2)
        legal_moves_1_3 = universe.get_legal_moves((1, 3))
        target = {north : (1, 2),
                  east  : (2, 3),
                  stop  : (1, 3)}
        self.assertEqual(target, legal_moves_1_3)
        legal_moves_2_3 = universe.get_legal_moves((2, 3))
        target = {north : (2, 2),
                  east  : (3, 3),
                  west  : (1, 3),
                  stop  : (2, 3)}
        self.assertEqual(target, legal_moves_2_3)
        # 3, 3 has the same options as 2, 3
        legal_moves_4_3 = universe.get_legal_moves((4, 3))
        target = {west  : (3, 3),
                  stop  : (4, 3)}
        self.assertEqual(target, legal_moves_4_3)

    def test_move_bot_exceptions(self):
        test_move_bot = (
            """ ######
                #  #0#
                # 3 ##
                #2  1#
                ###### """)
        universe = create_CTFUniverse(test_move_bot, 4)

        self.assertRaises(IllegalMoveException, universe.move_bot, 0, 'FOOBAR')

        self.assertRaises(IllegalMoveException, universe.move_bot, 0, north)
        self.assertRaises(IllegalMoveException, universe.move_bot, 0, west)
        self.assertRaises(IllegalMoveException, universe.move_bot, 0, south)
        self.assertRaises(IllegalMoveException, universe.move_bot, 0, east)

        self.assertRaises(IllegalMoveException, universe.move_bot, 1, north)
        self.assertRaises(IllegalMoveException, universe.move_bot, 1, east)
        self.assertRaises(IllegalMoveException, universe.move_bot, 1, south)

        self.assertRaises(IllegalMoveException, universe.move_bot, 2, west)
        self.assertRaises(IllegalMoveException, universe.move_bot, 2, south)

    def test_reset_bot_bot_positions(self):

        layout_chars = [wall, food, harvester, destroyer, free]

        test_reset_bot = (
            """ ########
                #0     #
                #2    3#
                #     1#
                ######## """)
        number_bots = 4
        universe = create_CTFUniverse(test_reset_bot, number_bots)
        self.assertEqual(str(universe),
                str(Layout(test_reset_bot, layout_chars, number_bots).as_mesh()))
        self.assertEqual(universe.bot_positions,
                [(1, 1), (6, 3), (1, 2), (6, 2)])
        test_shuffle = (
            """ ########
                #   0 3#
                # 1    #
                # 2    #
                ######## """)
        universe.bots[0]._move((4, 1))
        universe.bots[1]._move((2, 2))
        universe.bots[2]._move((2, 3))
        universe.bots[3]._move((6, 1))
        self.assertEqual(universe.bot_positions,
                [(4, 1), (2, 2), (2, 3), (6, 1)])
        self.assertEqual(str(universe),
                str(Layout(test_shuffle, layout_chars, number_bots).as_mesh()))
        universe.bots[0]._reset()
        universe.bots[1]._reset()
        universe.bots[2]._reset()
        universe.bots[3]._reset()
        self.assertEqual(str(universe),
                str(Layout(test_reset_bot, layout_chars, number_bots).as_mesh()))
        self.assertEqual(universe.bot_positions,
                [(1, 1), (6, 3), (1, 2), (6, 2)])

    def test_one(self):

        layout_chars = [wall, food, harvester, destroyer, free]

        test_start = (
            """ ######
                #0 . #
                #.  1#
                ###### """)
        number_bots = 2
        universe = create_CTFUniverse(test_start, number_bots)
        universe.move_bot(1, west)
        test_first_move = (
            """ ######
                #0 . #
                #. 1 #
                ###### """)
        self.assertEqual(str(universe),
                str(Layout(test_first_move, layout_chars, number_bots).as_mesh()))
        test_second_move = (
            """ ######
                #0 . #
                #.1  #
                ###### """)
        universe.move_bot(1, west)
        self.assertEqual(str(universe),
                str(Layout(test_second_move, layout_chars, number_bots).as_mesh()))
        test_eat_food = (
            """ ######
                #0 . #
                #1   #
                ###### """)
        self.assertEqual(universe.food_list, [(3, 1), (1, 2)])
        universe.move_bot(1, west)
        self.assertEqual(str(universe),
                str(Layout(test_eat_food, layout_chars, number_bots).as_mesh()))
        self.assertEqual(universe.food_list, [(3, 1)])
        self.assertEqual(universe.teams[1].score, 1)
        test_destruction = (
            """ ######
                #  . #
                #0  1#
                ###### """)
        universe.move_bot(0, south)
        self.assertEqual(str(universe),
                str(Layout(test_destruction, layout_chars , number_bots).as_mesh()))
        test_red_score = (
            """ ######
                #  0 #
                #   1#
                ###### """)
        universe.move_bot(0, north)
        universe.move_bot(0, east)
        universe.move_bot(0, east)
        self.assertEqual(str(universe),
                str(Layout(test_red_score, layout_chars, number_bots).as_mesh()))
        self.assertEqual(universe.food_list, [])
        self.assertEqual(universe.teams[0].score, 1)
        test_bot_suicide = (
            """ ######
                #0   #
                #   1#
                ###### """)
        universe.move_bot(0, east)
        universe.move_bot(0, south)
        self.assertEqual(str(universe),
                str(Layout(test_bot_suicide, layout_chars, number_bots).as_mesh()))

    def test_no_eat_own_food(self):
        test_start = (
            """ ######
                #0 . #
                #.  1#
                ###### """)
        number_bots = 2
        universe = create_CTFUniverse(test_start, number_bots)
        universe.move_bot(1, north)
        universe.move_bot(1, west)
        self.assertEqual(universe.food_list, [(3, 1), (1, 2)])


if __name__ == '__main__':
    unittest.main()

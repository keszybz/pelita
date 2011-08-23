#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
This file demonstrates setting up a server and two clients using local actor connections.
The order is important in this case (as is described in demo_simplegame.py).

A difference to the remote game in demo_simplegame is that now,
`client.autoplay_background` uses a background thread instead of a background
process. This background thread sometimes does not close on CTRL+C. In these
cases, pressing CTRL+Z and then entering ‘kill %%’ usually is the way to
get rid of the program.
"""

from pelita.simplesetup import SimpleClient, SimpleServer
from pelita.player import RandomPlayer, BFSPlayer, SimpleTeam, StoppingPlayer, NQRandomPlayer, BasicDefensePlayer

network = True

layout_top = """
################################
#   #. #.#.#       #     #.#.#3#
# # ##       ##  #   ###   #.#1#
"""

layout_bottom = """#0#.#   ###   #  ##       ## # #
#2#.#.#     #       #.#.# .#   #
################################
"""

layout_middle = """# # #. # ###    #### .#..# # # #
# # ## # ..# #   #   ##### # # #
# #    ##### ###   ###.#   # # #
# ## # ..#.  #.###       #   # #
# #. ##.####        #.####  ## #
# ##  ####.#        ####.## .# #
# #   #       ###.#  .#.. # ## #
# # #   #.###   ### #####    # #
# # # #####   #   # #.. # ## # #
# # # #..#. ####    ### # .# # #
"""

client = SimpleClient("the good ones", SimpleTeam(StoppingPlayer(), StoppingPlayer()), local=not network)
client.autoplay_background()

client2 = SimpleClient("the bad ones", SimpleTeam(StoppingPlayer(), StoppingPlayer()), local=not network)
client2.autoplay_background()

#server = SimpleServer(rounds=30, layoutfile="layouts/01_demo.layout", local=not network)

layout = layout_top + layout_middle * 10 + layout_bottom

import yappi
yappi.start()
server = SimpleServer(rounds=30, layout=layout, local=not network)
server.run_ascii()

yappi.print_stats()

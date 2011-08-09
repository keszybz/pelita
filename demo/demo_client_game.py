from pelita.player import RandomPlayer, BFSPlayer, SimpleTeam

from pelita.actors import ClientActor

import logging
from pelita.utils.colorama_wrapper import colorama

FORMAT = '[%(asctime)s,%(msecs)03d][%(name)s][%(levelname)s][%(funcName)s]' + colorama.Fore.MAGENTA + ' %(message)s' + colorama.Fore.RESET
#logging.basicConfig(format=FORMAT, datefmt="%H:%M:%S", level=logging.WARNING)

import random
import time

class SlowBFSPlayer(BFSPlayer):
    def get_move(self):
        move = super(SlowBFSPlayer, self).get_move()
        #if random.randint(0, 18) == 7:
        time.sleep(2)
        return move

clientActor = ClientActor("the good ones")
clientActor.register_team(SimpleTeam(BFSPlayer(), SlowBFSPlayer()))
clientActor.connect("pelita-main", host="", port=50007)

clientActor2 = ClientActor("the bad ones")
clientActor2.register_team(SimpleTeam(RandomPlayer(), RandomPlayer()))
clientActor2.connect("pelita-main", host="", port=50007)


try:
    while clientActor.actor_ref.is_alive:
        clientActor.actor_ref.join(1)
except KeyboardInterrupt:
    pass
finally:
    clientActor.actor_ref.stop()
    clientActor2.actor_ref.stop()
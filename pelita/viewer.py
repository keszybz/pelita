# -*- coding: utf-8 -*-

""" The observers. """

from pelita import datamodel

__docformat__ = "restructuredtext"


class AbstractViewer(object):
    def set_initial(self, universe):
        """ This method is called when the first universe is ready.
        """
        pass

    def observe(self, round_, turn, universe, events):
        raise NotImplementedError(
                "You must override the 'observe' method in your viewer")

class DevNullViewer(object):
    """ A viewer that simply ignores everything. """
    def set_initial(self, universe):
        pass

    def observe(self, round_, turn, universe, events):
        pass
import time


class AsciiViewer(AbstractViewer):
    def __init__(self):
        self.time = time.time()
        self.last = None
        self.thefile = open("saveddata-norandom-nonoise2", "w")

    def observe(self, round_, turn, universe, events):
        if self.last:
            self.thefile.write(str(time.time() - self.time) + " ")
            self.thefile.write(str(time.time() - self.last) + "\n")
            if round_ == 29:
                self.thefile.flush()

        self.last = time.time()

        print ("Round: %i Turn: %i Score: %i:%i"
        % (round_, turn, universe.teams[0].score, universe.teams[1].score))
        print ("Events: %r" % [str(e) for e in events])
        print universe.compact_str
        if datamodel.TeamWins in events:
            team_wins_event = events.filter_type(datamodel.TeamWins)[0]
            print ("Game Over: Team: '%s' wins!" %
            universe.teams[team_wins_event.winning_team_index].name)



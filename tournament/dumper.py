#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pelita.simplesetup import SimpleViewer
from pelita.viewer import AbstractViewer

from pelita.messaging.json_convert import json_converter

import yaml

class SavingViewer(AbstractViewer):
    def __init__(self, stream):
        self.stream = stream

    def set_initial(self, universe):
        f.write("-\n")
        f.write("  universe:%s\n" % json_converter.dumps(universe))

    def observe(self, round_, turn, universe, events):
        obj = {
            "round": round_,
            "turn": turn,
            "universe": universe,
            "events": events
        }

        f.write("-\n")
        f.write("  round:%s\n" % json_converter.dumps(round_))
        f.write("  turn:%s\n" % json_converter.dumps(turn))
        f.write("  universe:%s\n" % json_converter.dumps(universe))
        f.write("  events:%s\n" % json_converter.dumps(events))

f = open("dump.yaml", "w")

viewer = SavingViewer(f)

tk_viewer = SimpleViewer()
tk_viewer.run_general(viewer)


from pelita.messaging import actor_of, RemoteConnection
from pelita.actors import ServerActor
import logging
from pelita.ui.tk_viewer import TkViewer

from pelita.utils.colorama_wrapper import colorama

FORMAT = '[%(asctime)s,%(msecs)03d][%(name)s][%(levelname)s][%(funcName)s]' + colorama.Fore.MAGENTA + ' %(message)s' + colorama.Fore.RESET
#logging.basicConfig(format=FORMAT, datefmt="%H:%M:%S", level=logging.WARNING)

server = actor_of(ServerActor, "pelita-main")


remote = RemoteConnection().start_listener(host="", port=50007)
remote.register("pelita-main", server)
remote.start_all()

#server.start()

layout = (
        """ ##################
            #0#.  . 2# .   3 #
            # #####    ##### #
            #     . #  .  .#1#
            ################## """)

server.notify("initialize_game", [layout, 4, 200])

viewer = TkViewer()
server.notify("register_viewer", [viewer])

import Tkinter
import ScrolledText

class InputMgr(Tkinter.Entry):
    def __init__(self, master):
        Tkinter.Entry.__init__(self, master)
        self.bind('<Return>', self.call_server)
        self.bind('<Up>', self.command_up)
        self.bind('<Down>', self.command_down)

        self.prev_commands_idx = 0
        self.prev_commands = [""]

        self.output = None

    def show_prev_command(self):
        command = self.prev_commands[self.prev_commands_idx % len(self.prev_commands)]
        self.delete(0, Tkinter.END)
        self.insert(0, command)

    def command_up(self, event):
        self.prev_commands_idx -= 1
        self.show_prev_command()
        return "break"

    def command_down(self, event):
        self.prev_commands_idx += 1
        self.show_prev_command()
        return "break"

    def call_server(self, event):
        print self.prev_commands, self.prev_commands_idx

        command = self.get()
        if not command:
            return
        if command in self.prev_commands:
            self.prev_commands.remove(command)
        self.prev_commands.append(command)
        self.prev_commands_idx = 0

        req = server.query(self.get())
        self.delete(0, Tkinter.END)
        self.output.insert("1.0", str(req.get(1)) + "\n")

class ReplWindow(Tkinter.Frame):
    def __init__(self, master=None):
        Tkinter.Frame.__init__(self, master)
        input_mgr = InputMgr(self)
        input_mgr.pack()

        lower_frame = Tkinter.Frame(self)
        team_mgr = Tkinter.Text(lower_frame)
        team_mgr.pack(side=Tkinter.LEFT)

        text_mgr = ScrolledText.ScrolledText(lower_frame)
        text_mgr.pack(side=Tkinter.LEFT)
        lower_frame.pack()

        input_mgr.output = text_mgr
        self.pack()

top = Tkinter.Toplevel()
top.title("Read Eval Print Loop")
repl = ReplWindow(top)

# input_queue


try:
    viewer.app.mainloop()
except KeyboardInterrupt:
    print "Received CTRL+C. Exiting."
finally:
    server.stop()
    remote.stop()

#remote.stop()

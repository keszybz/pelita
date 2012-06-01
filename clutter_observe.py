import sys
from gi.repository import Clutter, GObject
import zmq

def Stage():
    stage = Clutter.Stage()

    stage.set_size(400, 400)
    rect = Clutter.Rectangle()
    color = Clutter.Color()
    color.from_string('red')
    rect.set_color(color)
    rect.set_size(100, 100)
    rect.set_position(150, 150)

    timeline = Clutter.Timeline.new(3000)
    timeline.set_loop(True)

    alpha = Clutter.Alpha.new_full(timeline, Clutter.AnimationMode.EASE_IN_OUT_SINE)
    rotate_behaviour = Clutter.BehaviourRotate.new(
        alpha, 
        Clutter.RotateAxis.Z_AXIS,
        Clutter.RotateDirection.CW,
        0.0, 359.0)
    rotate_behaviour.apply(rect)
    timeline.start()
    stage.add_actor(rect)

    stage.show_all()
    stage.connect('destroy', lambda stage: Clutter.main_quit())
    return stage, rotate_behaviour

def Socket(address):
    ctx = zmq.Context()
    sock = ctx.socket(zmq.SUB)
    sock.setsockopt(zmq.SUBSCRIBE, "")
    sock.connect(address)
    return sock

def zmq_callback(queue, condition, sock):
    print 'zmq_callback', queue, condition, sock

    while sock.getsockopt(zmq.EVENTS) & zmq.POLLIN:
        observed = sock.recv()
        print observed

    return True

def main():
    res, args = Clutter.init(sys.argv)
    print res
    if res != Clutter.InitError.SUCCESS:
        return 1

    stage, rotate_behaviour = Stage()
    print stage

    sock = Socket(sys.argv[-1])
    zmq_fd = sock.getsockopt(zmq.FD)
    GObject.io_add_watch(zmq_fd,
                         GObject.IO_IN|GObject.IO_ERR|GObject.IO_HUP,
                         zmq_callback, sock)

    return Clutter.main()

if __name__ == '__main__':
    sys.exit(main())

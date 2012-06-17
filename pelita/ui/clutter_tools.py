from contextlib import contextmanager
from gi.repository import Clutter

# stolen from http://git.gnome.org/browse/pyclutter/tree/introspection/Clutter.py?h=wip/introspection&id=e8d34ff25a451ca4fc62ff38e95b95726352212a

@contextmanager
def easing_state(self, duration=None, mode=None, delay=None):
    """Perform operations under specified easing_state

    @duration: The optional easing duration in ms
    @mode: The optional easing mode
    @delay: An optional delay in ms

    The easing_state() method allows a simple usage of Clutters
    implicit animation API using a Python contextmanager.

    To set an actors position to 100,100 and move it to 200,200 in 2s
    using a linear animation you can call:
    >>> my_actor.set_position(100, 100)
    >>> with my_actor.easing_state(2000, Clutter.AnimationMode.LINEAR):
    ...     my_actor.set_position(200, 200)

    Instead of:
    >>> my_actor.set_position(100, 100)
    >>> my_actor.save_easing_state()
    >>> my_actor.set_easing_duration(2000)
    >>> my_actor.set_easing_mode(Clutter.AnimationMode.LINEAR)
    >>> my_actor.set_position(200, 200)
    >>> my_actor.restore_easing_state()
    """
    self.save_easing_state()
    if duration is not None:
        self.set_easing_duration(duration)
    if mode is not None:
        self.set_easing_mode(mode)
    if delay is not None:
        self.set_easing_delay(delay)
    yield
    self.restore_easing_state()

def clutter_texture(filename, **kwargs):
        t = Clutter.Texture(filename=filename, **kwargs)
        width, height = t.get_size()
        if width == 0 or height == 0:
            raise ValueError("failed to load image: '%s'" % filename)
        return t

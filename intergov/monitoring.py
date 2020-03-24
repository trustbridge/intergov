import sys
from functools import wraps

import statsd
from intergov.loggers import logger
from intergov import conf as ig_conf


if ig_conf.STATSD_HOST:
    statsd.Connection.set_defaults(
        host=ig_conf.STATSD_HOST,
        port=ig_conf.STATSD_PORT,
        sample_rate=1,
        disabled=False
    )


def get_stack_size():
    """Get stack size for caller's frame.

    %timeit len(inspect.stack())
    8.86 ms ± 42.5 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
    %timeit get_stack_size()
    4.17 µs ± 11.5 ns per loop (mean ± std. dev. of 7 runs, 100000 loops each)
    """
    size = 2  # current frame and caller's frame always exist
    while True:
        try:
            sys._getframe(size)
            size += 1
        except ValueError:
            return size - 1  # subtract current frame


base_stack = get_stack_size() + 30


class statsd_timer():
    def __init__(self, counter_name):
        self.counter_name = counter_name

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not ig_conf.STATSD_HOST:
                result = func(*args, **kwargs)
                return result
            scl = statsd.Timer(ig_conf.STATSD_PREFIX)
            scl.start()
            result = None
            try:
                result = func(*args, **kwargs)
            except Exception:
                raise
            finally:
                scl.stop(self.counter_name)
            return result

        return wrapper


# def statsd_timer(counter_name):
#     def decorator(method):
#         @wraps(method)
#         def timed(*args, **kw):
#             if not ig_conf.STATSD_HOST:
#                 result = method(*args, **kw)
#                 return result
#             scl = statsd.Timer(ig_conf.STATSD_PREFIX)
#             scl.start()
#             result = None
#             try:
#                 result = method(*args, **kw)
#             except Exception:
#                 raise
#             finally:
#                 scl.stop(counter_name)
#             return result
#         return timed
#     return decorator


def statsd_gauge(name, value):
    try:
        if not isinstance(value, (float, int)):
            value = float(value)
        if not ig_conf.STATSD_HOST:
            return
        else:
            gauge = statsd.Gauge(ig_conf.STATSD_PREFIX)
            gauge.send(name, value)
    except Exception as e:
        logger.exception(e)


def statsd_counter(name, value):
    try:
        if not isinstance(value, (float, int)):
            value = float(value)
        if not ig_conf.STATSD_HOST:
            return
        else:
            counter = statsd.Counter(ig_conf.STATSD_PREFIX)
            counter.increment(name, value)
    except Exception as e:
        logger.exception(e)

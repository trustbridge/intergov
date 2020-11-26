"""
The monitoring module implements all possible monitoring backends (like Statsd or Cloudwatch)
which can be turned on and off for specific setups.
If the backend is not configured then no data is sent to it.
"""
import sys
import time
from functools import wraps

import boto3
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
            t0 = time.time()
            result = func(*args, **kwargs)
            tdiff = time.time() - t0
            if ig_conf.PRINT_CONSOLE_METRICS:
                print(f"\t{self.counter_name}:\t{tdiff*1000}ms")
            if ig_conf.STATSD_HOST:
                statsd_timer = statsd.Timer(ig_conf.STATSD_PREFIX)
                statsd_timer.send(self.counter_name, tdiff)
            if ig_conf.SEND_CLOUDWATCH_METRICS:
                _send_cloudwatch_metric(self.counter_name, tdiff * 1000, unit="Milliseconds")
            return result

        return wrapper


def statsd_gauge(name, value):
    raise NotImplementedError()


def _send_cloudwatch_metric(name, value, unit):
    try:
        cloudwatch = boto3.Session(
            aws_access_key_id=ig_conf.CW_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=ig_conf.CW_AWS_SECRET_ACCESS_KEY,
            region_name=ig_conf.AWS_REGION,
        ).client('cloudwatch')
        response = cloudwatch.put_metric_data(
            MetricData=[
                {
                    'MetricName': name,
                    'Dimensions': [
                        {
                            'Name': 'Env',
                            'Value': ig_conf.JURISDICTION
                        },
                    ],
                    'Unit': unit,  # 'Count' 'Milliseconds'
                    'Value': value
                },
            ],
            Namespace=ig_conf.CLOUDWATCH_NAMESPACE
        )
        if response.get("ResponseMetadata", {}).get("HTTPStatusCode") != 200:
            logger.warning("Unable to send CloudWatch metric - %s", response)
    except Exception as e:
        logger.exception(e)


def increase_counter(name, value=1):
    """
    Sends one-time counter to all backends configured for this setup
    """
    try:
        if not isinstance(value, (float, int)):
            value = float(value)
        if ig_conf.PRINT_CONSOLE_METRICS:
            print(f"\t{name}:\t{value}")
        if ig_conf.STATSD_HOST:
            counter = statsd.Counter(ig_conf.STATSD_PREFIX)
            counter.increment(name, value)
        if ig_conf.SEND_CLOUDWATCH_METRICS:
            _send_cloudwatch_metric(name, value, unit="Count")
    except Exception as e:
        logger.exception(e)

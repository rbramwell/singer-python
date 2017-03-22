import argparse
import collections
import datetime
import functools
import json
import os
import time

DATETIME_FMT = "%Y-%m-%dT%H:%M:%SZ"


def strptime(dtime):
    return datetime.datetime.strptime(dtime, DATETIME_FMT)


def strftime(dtime):
    return dtime.strftime(DATETIME_FMT)


def ratelimit(limit, every):
    def limitdecorator(func):
        times = collections.deque()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if len(times) >= limit:
                tim0 = times.pop()
                tim = time.time()
                sleep_time = every - (tim - tim0)
                if sleep_time > 0:
                    time.sleep(sleep_time)

            times.appendleft(time.time())
            return func(*args, **kwargs)

        return wrapper

    return limitdecorator


def chunk(array, num):
    for i in range(0, len(array), num):
        yield array[i:i + num]


def get_abs_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


def load_json(path):
    with open(path) as fil:
        return json.load(fil)


def load_schema(entity):
    return load_json(get_abs_path("schemas/{}.json".format(entity)))


def update_state(state, entity, dtime):
    if dtime is None:
        return

    if isinstance(dtime, datetime.datetime):
        dtime = strftime(dtime)

    if entity not in state:
        state[entity] = dtime

    if dtime >= state[entity]:
        state[entity] = dtime


def parse_args(required_config_keys):
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='Config file', required=True)
    parser.add_argument('-s', '--state', help='State file')
    args = parser.parse_args()

    config = load_json(args.config)
    check_config(config, required_config_keys)

    if args.state:
        state = load_json(args.state)
    else:
        state = {}

    return config, state


def check_config(config, required_keys):
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise Exception("Config is missing required keys: {}".format(missing_keys))
from functools import wraps
from datetime import datetime
from time import time


def token_check(type: str = 'cor'):
    def decor(func):
        @wraps(func)
        async def cor_wrapper(self, *args, **kwargs):
            if not self._creds or datetime.utcnow() >= self._creds.expiry:
                self.refresh_token()

            return await func(self, *args, **kwargs)

        @wraps(func)
        def gen_wrapper(self, *args, **kwargs):
            if not self._creds or datetime.utcnow() >= self._creds.expiry:
                self.refresh_token()

            return func(self, *args, **kwargs)

        if type == 'cor':
            return cor_wrapper
        else:
            return gen_wrapper

    return decor


def measure(func):
    @ wraps(func)
    async def time_it(*args, **kwargs):
        start = int(round(time() * 1000))
        try:
            return await func(*args, **kwargs)
        finally:
            dur = int(round(time() * 1000)) - start
            logger.debug(
                f"Total execution time {func.__name__}: {dur} ms")

    return time_it


def async_cache(ttl: int = 300):
    cache = {}

    def decorator(func):
        @ wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f'{func.__name__}({args}, {kwargs})'
            if cache_key in cache and cache[cache_key]['timestamp'] > time():
                logger.debug(
                    f'getting from cache {cache_key}')
                return cache[cache_key]['result']

            result = await func(*args, **kwargs)
            cache[cache_key] = {'result': result,
                                'timestamp': time() + ttl}
            return result

        return wrapper

    return decorator

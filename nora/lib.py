from contextlib import contextmanager


def shallow_cm(func):
    gen = func()
    condition = next(gen)
    try:
        err = next(gen)
    except StopIteration:
        err = None

    @contextmanager
    def cm(*args, **kwargs):
        try:
            if callable(condition):
                state = condition(*args, **kwargs)
            else:
                state = condition
            if not state:
                if err:
                    raise err
            yield
        finally:
            pass
    return cm

from contextlib import contextmanager
from .lib import shallow_cm
import tempfile
from urllib import request, error
import shutil
import os


@shallow_cm
def internet():
    def connection(url='https://www.google.com/'):
        try:
            with request.urlopen(url):
                return True
        except error.URLError:
            return False
    yield connection
    yield ConnectionError('it seems you don\'t have internet connection')


@shallow_cm
def yarn():
    yield shutil.which('yarn')
    yield ModuleNotFoundError('it seems yarn is not installed')


@shallow_cm
def executable():
    yield lambda prog: shutil.which(prog)
    yield ModuleNotFoundError('it seems programe is not installed')


@contextmanager
def private_space(dir=tempfile.gettempdir()):
    try:
        prv_wd = os.getcwd()
        tmp_dir = tempfile.TemporaryDirectory(dir=dir)
        os.chdir(tmp_dir.name)
        yield tmp_dir.name
    finally:
        os.chdir(prv_wd)
        tmp_dir.cleanup()

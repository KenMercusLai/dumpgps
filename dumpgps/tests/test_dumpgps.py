"""Sample unit test module."""
# pylint: disable=no-self-use,missing-docstring
from os.path import abspath, join, basename

from ..dumpgps import files_in_current_dir, files_in_subdirs


def test_files_in_current_dir():
    test_files = ['requirements.txt', 'docker-compose.yml']
    assert all([True
                if join(abspath('.'), i) in files_in_current_dir('.') else False
                for i in test_files])


def test_files_in_subdirs():
    test_files = ['requirements.txt', 'docker-compose.yml', 'dumpgps.py']
    files = [basename(i) for i in files_in_subdirs('.')]
    assert all([True
                if i in files else False
                for i in test_files])

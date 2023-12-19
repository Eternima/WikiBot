import pytest
import builtins
from unittest.mock import Mock
from WikiBot import time_convert


def test_time_convert_hours():
    for i in range(10):
        s = 'h' + str(i)
        assert time_convert(s) == 3600 * i


def test_time_convert_days():
    for i in range(10):
        s = 'd' + str(i)
        assert time_convert(s) == 3600 * 24 * i

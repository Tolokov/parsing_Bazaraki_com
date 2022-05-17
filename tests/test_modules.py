import pytest
from string import ascii_letters
from itertools import cycle
from time import sleep
from os import remove, path
from json import load
from async_version import SaveJson, ProxiesList, TimerDecorator


def test_save_json():
    case = {
        'a': '1',
        'b': '4342969734183514',
        'c': '-12345678901234.56789012',
        'd': '[[[[[]]]]]',
        'e': '\x19',
        'f': '\U0001f42e\U0001f42e\U0001F42D\U0001F42D',
    }
    instance = SaveJson('name', case)
    assert instance._name == 'name.json'
    assert instance.__str__() == 'name.json'
    assert path.exists(instance._name)
    json_file = open(instance._name, 'r')
    file = load(json_file)
    json_file.close()
    remove(instance._name)
    assert file['a'] == '1'
    assert file['b'] == '4342969734183514'
    assert file['c'] == '-12345678901234.56789012'
    assert file['d'] == '[[[[[]]]]]'
    assert file['e'] == '\x19'
    assert file['f'] == '\U0001f42e\U0001f42e\U0001F42D\U0001F42D'


def test_proxies_list_cycle():
    """Value Sequence Comparison"""
    from string import ascii_letters

    case = [f'{i}' for i in ascii_letters]
    instance = ProxiesList(case)
    for letter in case:
        assert instance() == letter

    instance = ProxiesList(case)
    for i in range(100000):
        assert instance() in case


case = [
    (int(), TypeError),
    (float(), TypeError),
    (None, TypeError),
    (bool(), TypeError),
    (dict(), StopIteration),
    (list(), StopIteration),
    (str(), StopIteration),
    (set(), StopIteration),
    (frozenset(), StopIteration),
]


@pytest.mark.parametrize('params, excepted_exception', case)
def test_cycle_exception(params, excepted_exception):
    with pytest.raises(excepted_exception):
        assert ProxiesList(params).__next__()


def test_cycle_exception_len():
    with pytest.raises(TypeError):
        assert len(ProxiesList(['abc']))


def test_cycle_substitution():
    case = [i for i in ascii_letters]
    for n in range(len(case)):
        assert ProxiesList(case)() == next(cycle(case))
        assert next(ProxiesList(case)) == next(cycle(case))


def test_timer_decorator_check_attributes():
    time = TimerDecorator(6 ** 6 ** 6)
    assert time.__class__.__name__ == 'TimerDecorator'
    assert hasattr(time, 'start')

    with pytest.raises(AttributeError):
        assert time.finish
        assert time.stop
        assert time.result_print

    time.__del__()
    assert hasattr(time, 'finish')
    assert hasattr(time, 'stop')
    assert hasattr(time, 'result_print')


def test_timer_decorator_microseconds():
    time = TimerDecorator(sleep(0.2))
    time.__del__()
    assert time.stop.microseconds <= 500_000
    assert time.stop.microseconds >= 0

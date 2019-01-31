import pytest

from safeparser.safe_env import SafeEnv


def test_can_create_safe_env_from_dict():
    SafeEnv({})


def test_safe_env_has_len():
    env = SafeEnv({'a': 0, '__hidden__': 0})

    assert len(env) == 1


def test_safe_env_can_get_the_value_associated_with_a_key():
    env = SafeEnv({'a': 0, '__hidden__': 0})

    assert env['a'] == 0

    with pytest.raises(KeyError):
        env['b']

    assert env.get('a') == 0
    assert env.get('b') == None
    assert env.get('c', 'default') == 'default'
    assert env.get('__hidden__') == None
    assert env.get('__another_hidden__') == None


def test_safe_env_fails_to_get_value_associated_with_double_underscore_keys():
    env = SafeEnv({'a': 0, '__hidden__': 0})

    with pytest.raises(KeyError):
        env['__hidden__']

    with pytest.raises(KeyError):
        env['__another_hidden__']


def test_put_in_safe_env_delegates_to_a_dict():
    inner = {}
    env = SafeEnv(inner)
    env['a'] = 1

    assert inner == {'a': 1}


def test_safe_env_rejects_double_underscore_keys():
    inner = {}
    env = SafeEnv(inner)

    with pytest.raises(KeyError):
        env['__hidden__'] = None

    with pytest.raises(KeyError):
        env.setdefault('__hidden__', None)

    assert inner == {}


def test_safe_env_can_delete_items():
    inner = {'a': 0, '__hidden__': 0}
    env = SafeEnv(inner)

    del env['a']

    assert len(env) == 0
    assert len(inner) == 1


def test_safe_env_fails_to_delete_items_with_double_underscore_keys():
    inner = {'a': 0, '__hidden__': 0}
    env = SafeEnv(inner)

    with pytest.raises(KeyError):
        del env['__hidden__']

    with pytest.raises(KeyError):
        del env['__another_hidden__']


def test_safe_env_can_test_for_keys():
    inner = {'a': 0, '__hidden__': 0}
    env = SafeEnv(inner)

    assert 'a' in env
    assert 'b' not in env
    assert '__hidden__' not in env
    assert '__another_hidden__' not in env


def test_can_iterate_over_keys():
    inner = {'a': 0, '__hidden__': 0}
    env = SafeEnv(inner)

    assert list(env) == ['a']


def test_can_clear_visible_keys():
    inner = {'a': 0, '__hidden__': 0}
    env = SafeEnv(inner)

    env.clear()

    assert inner == {'__hidden__': 0}


def test_can_get_item_iterator():
    inner = {'a': 0, '__hidden__': 0}
    env = SafeEnv(inner)

    assert list(env.items()) == [('a', 0)]


def test_safe_env_can_pop():
    inner = {'a': 0, '__hidden__': 0}
    env = SafeEnv(inner)

    env.pop('a')

    assert inner == {'__hidden__': 0}
    assert env.pop('a', 'default') == 'default'
    assert env.pop('__hidden__', 'default') == 'default'
    assert inner == {'__hidden__': 0}

    with pytest.raises(KeyError):
        env.pop('__hidden__')


def test_safe_env_can_popitem():
    inner = {'a': 0, '__hidden__': 0}
    env = SafeEnv(inner)

    item = env.popitem()

    assert item == ('a', 0)
    assert 'a' not in inner

    with pytest.raises(KeyError):
        env.popitem()


@pytest.fixture
def rand_string_creator():
    from random import choice

    chars = 'abcdefghijklmnopqrstuvwxyz'

    return lambda size: ''.join(choice(chars) for _ in range(size))


def test_safe_env_popitem_preserves_order(rand_string_creator):
    keys = ['__' + rand_string_creator(5) + '__' for _ in range(100)]
    keys = list(set(keys))  # Remove duplicates, if any, just to make sure

    inner = {'a': 0}
    for key in keys:
        inner[key] = key

    env = SafeEnv(inner)

    assert env.popitem() == ('a', 0)

    for key in reversed(keys):
        assert inner.popitem() == (key, key)


def test_safe_env_setdefault():
    inner = {'a': 0, '__hidden__': 0}
    env = SafeEnv(inner)

    env.setdefault('a', 'not-0')
    env.setdefault('b', 0)

    assert inner == {'a': 0, '__hidden__': 0, 'b': 0}

    with pytest.raises(KeyError):
        env.setdefault('__hidden__', 'not-0')

    with pytest.raises(KeyError):
        env.setdefault('__another_hidden__', 'not-0')


def test_safe_evn_can_bu_updated():
    inner = {'a': 0, '__hidden__': 0}
    env = SafeEnv(inner)

    env.update([('a', 1)])
    env.update({'b': 2}, c=3)

    assert inner == {'a': 1, 'b': 2, 'c': 3, '__hidden__': 0}

    env.update({'__hidden__': 'not-0'})
    env.update({'__another_hidden__': 0})

    assert inner == {'a': 1, 'b': 2, 'c': 3, '__hidden__': 0}


def test_safe_env_can_be_represented():
    inner = {'a': 0}
    env = SafeEnv(inner)
    
    assert repr(env) == 'SafeEnv({\'a\': 0})'
    
    inner['__self__'] = 0
    
    assert repr(env) == 'SafeEnv({\'a\': 0})'
    
    inner['__self__'] = inner
    
    assert repr(env) == 'SafeEnv({\'a\': 0})'
        
    inner['self'] = env
    
    assert repr(env) == 'SafeEnv({\'a\': 0, \'self\': SafeEnv({...})})'

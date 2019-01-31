import pytest

from safeparser.plugins import PluginStore


@pytest.fixture
def plugin_store():
    return PluginStore()


def test_can_register_plugins(plugin_store):
    assert not plugin_store.has('fn')

    @plugin_store.register
    def fn(x): pass

    assert plugin_store.has('fn')
    assert plugin_store.get('fn') is fn


def test_can_register_with_custom_name(plugin_store):
    @plugin_store.register(name='custom')
    def fn(x): pass

    assert plugin_store.has('custom')
    assert plugin_store.get('custom') is fn


def test_can_give_zero_args_to_decorator(plugin_store):
    @plugin_store.register
    def fn1(x): pass

    @plugin_store.register()
    def fn2(x): pass

    assert plugin_store.has('fn1')
    assert plugin_store.has('fn2')


def test_plugins_can_be_registered_with_the_add_method(plugin_store):
    plugin_store.add(len)

    assert plugin_store.has('len')
    assert plugin_store.get('len') is len


def test_plugins_registered_with_the_add_method_can_have_custom_names(plugin_store):
    plugin_store.add(len, 'my_len')

    assert plugin_store.has('my_len')
    assert plugin_store.get('my_len') is len


def test_plugins_can_be_values(plugin_store):
    random_number = 4  # Chosen by fair dice roll. Guaranteed to be random.
    plugin_store.add(random_number, 'random_number')

    assert plugin_store.get('random_number') == random_number


def test_plugins_can_be_classes(plugin_store):
    @plugin_store.register
    class MyClass:
        def __init__(self, arg):
            self.arg = arg

    assert plugin_store.get('MyClass') is MyClass

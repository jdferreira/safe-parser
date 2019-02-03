import os
import textwrap

import pytest

from safeparser.parser import Parser, ParserException
from safeparser.plugins import PluginStore


@pytest.fixture
def parser():
    return Parser()


def test_parsers_can_parse_strings(parser):
    parser.parse('a = 0')

    assert parser.env == {'a': 0}


def test_parse_method_returns_the_environment(parser):
    assert parser.parse('a = 0') == {'a': 0}


def test_parsers_can_parse_files(parser, tmp_path):
    path = tmp_path / 'tmp.txt'
    path.write_text('a = 0')
    with path.open() as f:
        parser.parse(f)

    assert parser.env == {'a': 0}


def test_parsers_can_parse_multiple_inputs(parser):
    parser.parse('a = 0')
    parser.parse('b = 1')

    assert parser.env == {'a': 0, 'b': 1}


def test_parsers_accept_an_environment():
    parser = Parser(env={'a': 0})

    assert parser.env == {'a': 0}


def test_parsers_accept_a_plugin_store():
    store = PluginStore()
    parser = Parser(plugin_store=store)

    assert parser.plugin_store is store


def test_parsers_have_a_plugin_store(parser):
    assert isinstance(parser.plugin_store, PluginStore)


def test_python_syntax_errors_are_converted_to_parser_exceptions():
    bad_inputs = [
        'a b',
        'def = 1',
        'def',
        '= 1',
        '+++',
    ]

    for arg in bad_inputs:
        parser = Parser()

        with pytest.raises(ParserException):
            parser.parse(arg)
            pytest.fail(f'Failed to reject {arg!r}')

        assert parser.env == {}


def test_parsers_accept_safe_values(parser):
    parser.parse(textwrap.dedent('''
        valid = [
            None,
            False,
            True,
            0,
            1.0,
            '',
            [],
            {''},
            {'': 0},
        ]
    '''))

    assert parser.env['valid'] == [
        None,
        False,
        True,
        0,
        1.0,
        '',
        [],
        {''},
        {'': 0},
    ]


def test_parsers_reject_valid_python_syntax_that_is_unsafe(parser):
    bad_inputs = [
        'import os',
        'fn(x=lambda: None)',
        'list.append(1, b=2)',
        'eval("0")',
        'exec("a = 0")',
        'def fn(): pass',
        'class A: pass',
        'for i in []: pass',
        'if i: pass',
        'a, b = [1, 2]',
        'a = b = 0',
        'print("")',
        'with fn() as f: pass',
        '1 + 1',
        'a = 1 + 1',
    ]

    for arg in bad_inputs:
        with pytest.raises(ParserException):
            parser.parse(arg)
            pytest.fail(f'Failed to reject {arg!r}')

        assert parser.env == {}


def test_cannot_overwrite_existing_variables(parser):
    with pytest.raises(ParserException):
        parser.parse(textwrap.dedent('''
            a = []
            a = None
        '''))

    assert parser.env == {'a': []}


def test_plugin_names_are_illegal_entity_names(parser):
    parser.plugin_store.add(len)

    with pytest.raises(ParserException):
        parser.parse('len = 0')

    assert parser.env == {}


def test_parsers_reject_double_underscore_variable_names(parser):
    parser.parse('__abc = 0')
    parser.parse('abc__ = 0')

    with pytest.raises(ParserException):
        parser.parse('__abc__ = 0')

    assert parser.env == {'__abc': 0, 'abc__': 0}


def test_parsers_can_use_previously_defined_variables(parser):
    parser.parse(textwrap.dedent('''
        a = 0
        b = 1
        c = [a, b]
    '''))

    assert parser.env == {
        'a': 0,
        'b': 1,
        'c': [0, 1],
    }


def test_parsers_do_not_execute_unregistered_plugins(parser):
    with pytest.raises(ParserException):
        parser.parse('a = len([])')

    assert parser.env == {}


def test_parsers_execute_registered_plugins(parser):
    parser.plugin_store.add(len)

    parser.parse('a = len([])')

    assert parser.env == {'a': 0}


def test_parsers_can_assign_plugins_to_variables(parser):
    parser.plugin_store.add(len)

    parser.parse('fn = len')

    assert parser.env == {'fn': len}


def test_parsers_can_only_execute_plugins_by_their_registered_name(parser):
    parser.plugin_store.add(len)

    with pytest.raises(ParserException):
        parser.parse(textwrap.dedent('''
            fn = len
            a = fn([])
        '''))

    assert parser.env == {'fn': len}


def test_parser_executes_function_calls(parser):
    l = []

    @parser.plugin_store.register
    def fn():
        l.append(0)

    parser.parse('fn()')

    assert l == [0]


def test_parser_plugins_have_access_to_the_env(parser):
    @parser.plugin_store.register
    def make_all_pairs(*, env):
        return [
            (val1, val2)
            for key1, val1 in env.items()
            for key2, val2 in env.items()
            if key1 < key2
        ]

    parser.parse(textwrap.dedent('''
        a = 1
        b = 2
        c = 3
        d = make_all_pairs()
    '''))

    assert parser.env['d'] == [(1, 2), (1, 3), (2, 3)]


def test_parser_plugins_cannot_access_or_create_double_underscore_variables(parser):
    @parser.plugin_store.register
    def fn1(*, env):
        a = env['__env__']

    @parser.plugin_store.register
    def fn2(*, env):
        env['__a__'] = 0

    with pytest.raises(KeyError):
        parser.parse('fn1()')

    with pytest.raises(KeyError):
        parser.parse('fn2()')

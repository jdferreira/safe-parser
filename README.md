# Safe Parser

Python's standard library provides a function, `ast.literal_eval`, which safely evaluates string representation of a python literal, such as a list or a string. This allows one to parse, for example, `'["string", {}, 12.34]'` and other such safe literals.

This package provides an improvement of that ideia.

A safe parser is an object that can take a string containing a valid python code that contains  assignments, and produces a dictionary of the resulting where environment dictionary. As such, it permits parsing and executing this:
```python
a = ['a', 'list']
b = {'content': a}
```
which is parsed into the following:
```python
{
    'a': ['a', 'list'],
    'b': {'content': ['a', 'list']}
}
```

The parser also allows executing functions, as long as it knows that they are safe to execute. For example, if there is a function 
```python
def repeat(x, n):
    return [x] * n
```
then a parser can parse the string `a = repeat('x', 3)` into:
```python
{
    'a': ['x', 'x', 'x']
}
```

The safety is guaranteed becuase the parser is aware of which functions are safe to execute, by using a plugin system. All parsers contain a (initially empty) plugin store, which can be used to register new plugins:
```python
from safeparser import Parser

parser = Parser()

@parser.plugin_store.register
def repeat(x, n):
    return [x] * n

parser.parse('a = repeat("x", 3)')

print(parser.env)

# output: {'a': ['x', 'x', 'x']}
```

## Motivation

The parser provided with this package enables, foremost, the ability to run user input in a safe and controlled manner. Python, as a general purpose programming language, can "execute anything", and as such is not appropriate for user input. However, there are situations where a system is so complex that users may need the ability to talk more expressively with a third party.

The primary goal of this package is to serve as a user input processor for a system that allows users to ask a server to call a function with a series of input values. For example, a user may be interested in the similarity between any pair of a set of provided entities. Thus, the user needs to provide the entities and the pairs. For _n_ complex entities, this would mean providing _O_(_n<sup>2</sup>_) pairs, which may be impractical. If the system knows how to make the pairs itself, then the user does needs only to provide the entities.

## What is safe?

For the purposes of this package, a safe statement is one that, once executed, produces no visible side effect other than creating or editing a variable (or multiple variables) in a dictionary.

## Features

- A parser can parse strings and file objects. The following two are valid
```python
parser.parse('a = 1')
with open('filename.txt') as f:
    parser.parse(f)
```

- A parser can parse multiple inputs, each one building on top of the resulting dictionray of the previous
```python
parser.parse('a = 1')
parser.parse('b = 2')
print(parser.env)
# output: {'a': 1, 'b': 2}
```

- A parser can be started with an existing environment
```python
parser = Parser(env={'a': 1})
parser.parse('b = a')
print(parser.env)
# output: {'a': 1, 'b': 1}
```

- A plugin can be registered using a decorator or a method. The following are equivalent
```python
@parser.plugin_store.register
def add(a, b):
    return a + b

def add(a, b):
    return a + b
parser.plugin_store.add(add)
```

- Plugins have direct access to the environment being constructed and can alter it
```python
@parser.plugin_store.register
def new_variable(*, env):
    env['var'] = 0
```
For this to work, the plugin function must have a non-optional keyword-only argument named `env`. Note that the environment is not a python dictionary, but it behaves like one, except that it does not allow double-underscore variables (see limitations below), and that the methods `keys()` and `values()` are not implemented.


## Limitations

- Because of how the code works, and also to not hinder future development, double-underscore variable names are not allowed. This is, on the one hand, so that we can safely inject an empty `__builtins__` into the evaluation of the code, as well as to allow injecting the current environment's state into plugins that request it (see above).

- At the moment, I am not allowing expressions other than calls and literal. This means that the input does not allow binray operation, for example, unlike the `ast.literal_eval` function.

- Methods cannot be executed. It is impossible to execute
```python
l = []
l.append(0)
```
even though this is safe from the definition above

- Note that plugins are only safe as long as the code they execute is safe. However, since the parser itself is in control of what plugins it supports, the ideia of executing unsafe user-provided code is still impossible.

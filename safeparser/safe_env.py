from itertools import chain

_SENTINEL = object()


class SafeEnv:
    @classmethod
    def hidden(cls, key):
        return key.startswith('__') and key.endswith('__')

    @classmethod
    def process_args(cls, mapping=(), **kwargs):
        if hasattr(mapping, 'items'):
            mapping = mapping.items()

        return (
            (key, value)
            for key, value in chain(mapping, kwargs.items())
            if not cls.hidden(key)
        )

    def __init__(self, inner):
        self.inner = inner

    def __len__(self):
        return sum(1 for key in self.inner.keys() if not self.hidden(key))

    def __getitem__(self, key):
        if self.hidden(key):
            raise KeyError(f'Unsafe key: {key}')

        return self.inner.__getitem__(key)

    def __setitem__(self, key, val):
        if self.hidden(key):
            raise KeyError(f'Unsafe key {key}')

        return self.inner.__setitem__(key, val)

    def __delitem__(self, key):
        if self.hidden(key):
            raise KeyError(f'Unsafe key: {key}')

        return self.inner.__delitem__(key)
    
    def __contains__(self, key):
        return not self.hidden(key) and key in self.inner
    
    def __iter__(self):
        return (key for key in self.inner if not self.hidden(key))
    
    def get(self, key, default=None):
        if self.hidden(key):
            return default
        else:
            return self.inner.get(key, default)

    def clear(self):
        keys = list(self.inner)
        for key in keys:
            if not self.hidden(key):
                del self.inner[key]
    
    def items(self):
        return (
            (key, val)
            for key, val in self.inner.items()
            if not self.hidden(key)
        )
    
    def pop(self, key, val=_SENTINEL):
        hidden_key = self.hidden(key)
        val_given = not val is _SENTINEL

        if val_given and hidden_key:
            return val
        elif val_given and not hidden_key:
            return self.inner.pop(key, val)
        elif not val_given and hidden_key:
            raise KeyError(f'Unsafe key: {key}')
        elif not val_given and not hidden_key:
            return self.inner.pop(key)

    def popitem(self):
        # Pop and collect items from the inner dict until we find one that is
        # not hidden. When we do so, put back the collected items into the inner
        # dict in the reverse order. This ensures that the order guarantees of
        # dicts in python 3.7 are kept.
        
        collected = []
        result = None
        
        while self.inner:
            item = self.inner.popitem()
            if self.hidden(item[0]):
                collected.append(item)
            else:
                result = item
                break
        
        for key, val in reversed(collected):
            self.inner[key] = val
        
        if result is None:
            raise KeyError
        else:
            return result

    def setdefault(self, key, default=None):
        if self.hidden(key):
            raise KeyError(f'Unsafe key {key}')

        return self.inner.setdefault(key, default)

    def update(self, mapping=(), **kwargs):
        self.inner.update(self.process_args(mapping, **kwargs))

    def repr_item(self, key, value):
        if value is self:
            return type(self).__name__ + '({...})'
        else:
            return repr(value)
    
    def __repr__(self):
        name = type(self).__name__
        
        inner = '{' + ', '.join(
            f'{key!r}: {self.repr_item(key, value)}'
            for key, value in self.items()
        ) + '}'

        return f'{name}({inner})'



# TODO
# We're missing the `keys` and `values` methods, which should return views into
# the dictionary without the hidden keys. This will be implemented, if
# necessary, later.

# TODO
# As implemented, this class allows subclassing and changing the `hidden` class
# method, which allows other types of criteria for hiding keys. This is not
# tested, and should be.

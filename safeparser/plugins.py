class PluginStore:

    def __init__(self):
        self.plugins = {}

    def add(self, arg, name=None):
        name = name or arg.__name__
        self.plugins[name] = arg

    def register(self, fn=None, *, name=None):
        def wrapper(fn):
            self.add(fn, name)
            return fn

        if fn is not None:
            return wrapper(fn)
        else:
            return wrapper

    def has(self, arg):
        return arg in self.plugins

    def clear(self):
        self.plugins.clear()

    def get(self, name):
        return self.plugins[name]

import ast
import inspect

from safeparser.plugins import PluginStore
from safeparser.safe_env import SafeEnv


class ParserException(Exception):
    pass


class EnvironmentInjector(ast.NodeVisitor):

    def __init__(self, plugin_store):
        self.plugin_store = plugin_store

    def visit_Call(self, node):
        identifier = node.func.id

        if not self.plugin_store.has(identifier):
            return

        plugin = self.plugin_store.get(identifier)

        if not callable(plugin):
            return

        kwonlyargs = inspect.getfullargspec(plugin).kwonlyargs

        if 'env' in kwonlyargs:
            env_node = ast.Name('__env__', ast.Load())
            env_node.lineno = 0
            env_node.col_offset = 0

            node.keywords.append(
                ast.keyword(arg='env', value=env_node)
            )


class SafeCodeValidator(ast.NodeVisitor):

    def __init__(self, plugin_store):
        self.plugin_store = plugin_store

    def visit_Module(self, node):
        for stmt in node.body:
            self.visit(stmt)

    def visit_Expr(self, node):
        if not isinstance(node.value, ast.Call):
            raise ParserException(
                f'l.{node.lineno}: Illegal syntax'
            )

        self.visit_Call(node.value)

    def visit_Call(self, node):
        if not isinstance(node.func, ast.Name):
            raise ParserException(
                f'l.{node.lineno}: Illegal syntax'
            )

        for arg in node.args:
            self.visit(arg)

        for kw in node.keywords:
            self.visit(kw.value)

    def visit_Assign(self, node):
        if len(node.targets) > 1:
            # a = b = c
            raise ParserException(
                f'l.{node.lineno}: Illegal syntax'
            )

        if not isinstance(node.targets[0], ast.Name):
            # a, b = c
            raise ParserException(
                f'l.{node.lineno}: Illegal syntax'
            )

        identifier = node.targets[0].id

        if self.plugin_store.has(identifier):
            # Disallow overwriting plugins
            raise ParserException(
                f'l.{node.lineno}: Illegal assignment into plugin {identifier}'
            )

        if identifier.startswith('__') and identifier.endswith('__'):
            # Disallow variables that start and end with double underscores.
            # This is to ensure that __builtins__, __env__ and other future
            # implementation specific features do not collide with user-defined
            # input
            raise ParserException(
                f'l.{node.lineno}: Illegal assignment into double-underscore variable {identifier}'
            )

        self.visit(node.value)

    def visit_List(self, node):
        for elt in node.elts:
            self.visit(elt)

    def visit_Set(self, node):
        for elt in node.elts:
            self.visit(elt)

    def visit_Dict(self, node):
        for key in node.keys:
            self.visit(key)

        for val in node.values:
            self.visit(val)

    def visit_Num(self, node):
        pass

    def visit_NameConstant(self, node):
        pass

    def visit_Str(self, node):
        pass

    def visit_Name(self, node):
        pass

    def generic_visit(self, node):
        raise ParserException(
            f'l.{node.lineno}: Illegal syntax'
        )


class Parser:

    def __init__(self, *, env=None, plugin_store=None):
        if env is None:
            env = {}

        if plugin_store is None:
            plugin_store = PluginStore()

        self.env = env
        self.plugin_store = plugin_store

    def parse(self, content):
        content = self.prepare_content(content)

        try:
            root = ast.parse(content, filename='')
        except SyntaxError as e:
            raise ParserException(e)

        SafeCodeValidator(self.plugin_store).visit(root)

        # Since we're using python's eval function to actually evaluate
        # expressions, we must ensure that no builtin python functions leak into
        # the environment. Also, there are other important preparations that
        # must be executed to the environment before actually evaluating the
        # content
        self.prepare_environment()

        try:
            self.execute(root)
        finally:
            # We do not want to report back the internal variables in the
            # environment; as such, we remove them here before the user has the
            # possibility of examining the environment
            self.strip_environment()

    def prepare_content(self, content):
        if isinstance(content, str):
            return content

        try:
            return content.read()
        except:
            raise ParserException(
                f'Cannot read the contents of a {type(content)} variable'
            )

    def prepare_environment(self):
        self.env['__builtins__'] = {}
        self.env['__env__'] = SafeEnv(self.env)

    def strip_environment(self):
        del self.env['__builtins__']
        del self.env['__env__']

    def execute(self, root):
        for stmt in root.body:
            if isinstance(stmt, ast.Assign):
                self.execute_assign(stmt)
            elif isinstance(stmt, ast.Expr):
                self.execute_expr(stmt)
            else:
                raise ParserException(
                    f'l.{stmt.lineno}: Illegal syntax'
                )

    def execute_assign(self, stmt):
        identifier = stmt.targets[0].id

        if identifier in self.env:
            # Disallow overwriting variables
            raise ParserException(
                f'l.{stmt.lineno}: Illegal assignment into existing variable {identifier}'
            )

        self.env[identifier] = self.evaluate_expr(stmt.value)

    def execute_expr(self, stmt):
        return self.evaluate_expr(stmt.value)

    def evaluate_expr(self, expr):
        if isinstance(expr, ast.Call):
            if not self.plugin_store.has(expr.func.id):
                raise ParserException(
                    f'l.{expr.lineno}: Unknown plugin {expr.func.id}'
                )

        try:
            globals = {}
            globals.update(self.env)
            globals.update(self.plugin_store.plugins)

            return eval(self.compile_expr(expr), globals)
        except NameError as ex:
            raise ParserException(ex)

    def compile_expr(self, expr):
        EnvironmentInjector(self.plugin_store).visit(expr)

        code = ast.Expression(body=expr)
        code.lineno = expr.lineno
        code.col_offset = expr.col_offset

        return compile(code, '<string>', 'eval')

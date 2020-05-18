from ast import NodeTransformer

try:
    from ast import unparse
except ImportError:
    from astunparse import unparse

# TODO Try Python 3.9 and use ast.unparse
# see https://docs.python.org/3.9/library/ast.html#ast.unparse

# TODO figure out how to get an AST object from the mpc nodes extracted out


def ast_to_dict():
    raise NotImplementedError


def _vyper_only_source_code(ast_node):
    return unparse(ast_node)


# TODO: rename ...
# class CodeExtractor(NodeTransformer):
class Transformer(NodeTransformer):
    def __init__(self):
        self.mpc_nodes = []

    def visit_AsyncFunctionDef(self, node):  # noqa N802
        self.generic_visit(node)
        for dec in node.decorator_list:
            if dec.id == "mpc":
                self.mpc_nodes.append(node)
                return None


# TODO rename ...
# class to make the code executable
#
# * remove @mpc decorator
# * ...
class RemoveDecorator(NodeTransformer):
    def __init__(self):
        self.mpc_nodes = []

    def visit_AsyncFunctionDef(self, node):  # noqa N802
        self.generic_visit(node)
        for dec in node.decorator_list:
            if dec.id == "mpc":
                self.mpc_nodes.append(node)
                return None

import ast

from astunparse import unparse

from vyper.ast.pre_parser import pre_parse

from mpc.ast import Transformer


class RatelCompiler:
    def __init__(self, *, node_transformer_class=None):
        if node_transformer_class is None:
            node_transformer_class = Transformer
        self.node_transformer = node_transformer_class()

    def extract_vyper_code(self, contract_code):
        class_types, reformatted_code = pre_parse(contract_code)
        vyper_code_tree = ast.parse(reformatted_code)
        self.node_transformer.visit(vyper_code_tree)
        return unparse(vyper_code_tree)

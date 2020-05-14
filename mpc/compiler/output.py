"""Functions to build the MPC output."""
from mpc.ast import ast_to_dict
from vyper.compiler.phases import CompilerData


def build_ast_dict(compiler_data: CompilerData) -> dict:
    ast_dict = {
        "contract_name": compiler_data.contract_name,
        "ast": ast_to_dict(compiler_data.vyper_module),
    }
    return ast_dict

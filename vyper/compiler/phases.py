import copy
import warnings
from typing import Optional, Tuple

from vyper import ast as vy_ast
from vyper import compile_lll, optimizer
from vyper.parser import parser
from vyper.parser.global_context import GlobalContext
from vyper.typing import InterfaceImports


class SuperCompiler:
    """Class to handle multiple "types" of ``CompilerData``.

    This is for the case in which a contract contains programming constructs
    external to the vyper domain for interoperability with other systems
    for example.

    As an example, a contract could contain MPC programs that ought to be
    executed by an MPC network. The vyper contract may act as a coordinator
    (trusted party) to help in the execution of the MPC protocol partially
    described in the contract. The ``SuperCompiler`` would take care of
    compiling both the vyper contract and the MPC programs.

    In the context of the ``CompilerData`` used to handle the different
    compilation phases for vyper, the ``SuperCompiler`` acts as a point of
    entry to perform pre-compilation phases required for the vyper
    ``CompilerData`` to operate correctly, but also for the "MPC"
    ``CompilerData`` specific compilation phase handler.

    At the risk of being inacccurate, it may be useful to view this
    ``CompilerData`` as a compiler state machine. Hence, vyper has its
    own vyper compiler state machine, and the super compiler would
    allow running that compiler state machine but would also allow
    for the execution of other compiler state machines that would be
    provided in a perhaps "plugin" manner.

    The SuperCompiler, or Compiler Machine, or MetaCompiler, or whatever
    you want to call it, must first extract the vyper code and external
    codes. It seems easier to do so with an AST and hence, the SuperCompiler
    could:

    1. first get the AST for the "mixed" source code
    2. get the ast for the vyper code, its source code, and metadata
    3. get the ast for the mpc code, its source code, and metadata

    once the separation is done, the resulting pieces can be used by or
    fed to the specialized compiler machines (e.g. vyper and mpc).
    """

    def __init__(
        self,
        *compiler_machines,
        vyper_compiler_machine=None,
        source_code: str,
        contract_name: str = "VyperContract",
        interface_codes: Optional[InterfaceImports] = None,
        source_id: int = 0,
    ) -> None:
        self.compiler_machines = compiler_machines
        self.vyper_compiler_machine
        self.contract_name = contract_name
        self.source_code = source_code
        self.interface_codes = interface_codes
        self.source_id = source_id


class CompilerData:
    """
    Object for fetching and storing compiler data for a Vyper contract.

    This object acts as a wrapper over the pure compiler functions, triggering
    compilation phases as needed and providing the data for use when generating
    the final compiler outputs.

    Attributes
    ----------
    vyper_module : vy_ast.Module
        Top-level Vyper AST node
    vyper_module_folded : vy_ast.Module
        Folded Vyper AST
    global_ctx : GlobalContext
        Sorted, contextualized representation of the Vyper AST
    lll_nodes : LLLnode
        LLL used to generate deployment bytecode
    lll_runtime : LLLnode
        LLL used to generate runtime bytecode
    assembly : list
        Assembly instructions for deployment bytecode
    assembly_runtime : list
        Assembly instructions for runtime bytecode
    bytecode : bytes
        Deployment bytecode
    bytecode_runtime : bytes
        Runtime bytecode
    """

    def __init__(
        self,
        source_code: str,
        contract_name: str = "VyperContract",
        interface_codes: Optional[InterfaceImports] = None,
        source_id: int = 0,
    ) -> None:
        """
        Initialization method.

        Arguments
        ---------
        source_code : str
            Vyper source code.
        contract_name : str, optional
            The name of the contract being compiled.
        interface_codes: Dict, optional
            Interfaces that may be imported by the contracts during compilation.
            * Formatted as as `{'interface name': {'type': "json/vyper", 'code': "interface code"}}`
            * JSON interfaces are given as lists, vyper interfaces as strings
        source_id : int, optional
            ID number used to identify this contract in the source map.
        """
        self.contract_name = contract_name
        self.source_code = source_code
        self.interface_codes = interface_codes
        self.source_id = source_id

    @property
    def vyper_code(self) -> str:
        if not hasattr(self, "_vyper_code"):
            self._vyper_code = extract_vyper_code(self.source_code, self.source_id)
        return self.vyper_code

    @property
    def vyper_module(self) -> vy_ast.Module:
        if not hasattr(self, "_vyper_module"):
            self._vyper_module = generate_ast(self.source_code, self.source_id)
            # self._vyper_module = generate_ast(self.vyper_code, self.source_id)

        return self._vyper_module

    @property
    def vyper_module_folded(self) -> vy_ast.Module:
        if not hasattr(self, "_vyper_module_folded"):
            self._vyper_module_folded = generate_folded_ast(self.vyper_module)

        return self._vyper_module_folded

    @property
    def global_ctx(self) -> GlobalContext:
        if not hasattr(self, "_global_ctx"):
            self._global_ctx = generate_global_context(
                self.vyper_module_folded, self.interface_codes
            )

        return self._global_ctx

    def _gen_lll(self) -> None:
        # fetch both deployment and runtime LLL
        self._lll_nodes, self._lll_runtime = generate_lll_nodes(
            self.source_code, self.global_ctx
        )

    @property
    def lll_nodes(self) -> parser.LLLnode:
        if not hasattr(self, "_lll_nodes"):
            self._gen_lll()
        return self._lll_nodes

    @property
    def lll_runtime(self) -> parser.LLLnode:
        if not hasattr(self, "_lll_runtime"):
            self._gen_lll()
        return self._lll_runtime

    @property
    def assembly(self) -> list:
        if not hasattr(self, "_assembly"):
            self._assembly = generate_assembly(self.lll_nodes)
        return self._assembly

    @property
    def assembly_runtime(self) -> list:
        if not hasattr(self, "_assembly_runtime"):
            self._assembly_runtime = generate_assembly(self.lll_runtime)
        return self._assembly_runtime

    @property
    def bytecode(self) -> bytes:
        if not hasattr(self, "_bytecode"):
            self._bytecode = generate_bytecode(self.assembly)
        return self._bytecode

    @property
    def bytecode_runtime(self) -> bytes:
        if not hasattr(self, "_bytecode_runtime"):
            self._bytecode_runtime = generate_bytecode(self.assembly_runtime)
        return self._bytecode_runtime


def _generate_py_asts(source_code: str, source_id: int) -> vy_ast.Module:
    """
    Generate python ASTs from source code.

    This is a preliminary phase of compilation.

    Arguments
    ---------
    source_code : str
        Vyper source code.
    source_id : int
        ID number used to identify this contract in the source map.

    Returns
    -------
    vy_ast.Module
        Top-level Vyper AST node
    """
    return vy_ast.parse_to_ast(source_code, source_id)


def generate_ast(source_code: str, source_id: int) -> vy_ast.Module:
    """
    Generate a Vyper AST from source code.

    Arguments
    ---------
    source_code : str
        Vyper source code.
    source_id : int
        ID number used to identify this contract in the source map.

    Returns
    -------
    vy_ast.Module
        Top-level Vyper AST node
    """
    return vy_ast.parse_to_ast(source_code, source_id)


def generate_folded_ast(vyper_module: vy_ast.Module) -> vy_ast.Module:
    """
    Perform constant folding operations on the Vyper AST.

    Arguments
    ---------
    vyper_module : vy_ast.Module
        Top-level Vyper AST node

    Returns
    -------
    vy_ast.Module
        Folded Vyper AST
    """
    vyper_module_folded = copy.deepcopy(vyper_module)
    vy_ast.folding.fold(vyper_module_folded)

    return vyper_module_folded


def generate_global_context(
    vyper_module: vy_ast.Module, interface_codes: Optional[InterfaceImports],
) -> GlobalContext:
    """
    Generate a contextualized AST from the Vyper AST.

    Arguments
    ---------
    vyper_module : vy_ast.Module
        Top-level Vyper AST node
    interface_codes: Dict, optional
        Interfaces that may be imported by the contracts.

    Returns
    -------
    GlobalContext
        Sorted, contextualized representation of the Vyper AST
    """
    return GlobalContext.get_global_context(
        vyper_module, interface_codes=interface_codes
    )


def generate_lll_nodes(
    source_code: str, global_ctx: GlobalContext
) -> Tuple[parser.LLLnode, parser.LLLnode]:
    """
    Generate the intermediate representation (LLL) from the contextualized AST.

    This phase also includes LLL-level optimizations.

    This function returns two values, one for generating deployment bytecode and
    the other for generating runtime bytecode. The remaining compilation phases
    may be called with either value, depending on the desired final output.

    Arguments
    ---------
    source_code : str
        Vyper source code.
    global_ctx : GlobalContext
        Contextualized Vyper AST

    Returns
    -------
    (LLLnode, LLLnode)
        LLL to generate deployment bytecode
        LLL to generate runtime bytecode
    """
    lll_nodes, lll_runtime = parser.parse_tree_to_lll(source_code, global_ctx)
    lll_nodes = optimizer.optimize(lll_nodes)
    lll_runtime = optimizer.optimize(lll_runtime)
    return lll_nodes, lll_runtime


def generate_assembly(lll_nodes: parser.LLLnode) -> list:
    """
    Generate assembly instructions from LLL.

    Arguments
    ---------
    lll_nodes : str
        Top-level LLL nodes. Can be deployment or runtime LLL.

    Returns
    -------
    list
        List of assembly instructions.
    """
    assembly = compile_lll.compile_to_assembly(lll_nodes)
    if _find_nested_opcode(assembly, "DEBUG"):
        warnings.warn(
            "This code contains DEBUG opcodes! The DEBUG opcode will only work in "
            "a supported EVM! It will FAIL on all other nodes!"
        )
    return assembly


def _find_nested_opcode(assembly, key):
    if key in assembly:
        return True
    else:
        sublists = [sub for sub in assembly if isinstance(sub, list)]
        return any(_find_nested_opcode(x, key) for x in sublists)


def generate_bytecode(assembly: list) -> bytes:
    """
    Generate bytecode from assembly instructions.

    Arguments
    ---------
    assembly : list
        Assembly instructions. Can be deployment or runtime assembly.

    Returns
    -------
    bytes
        Final compiled bytecode.
    """
    return compile_lll.assembly_to_evm(assembly)[0]

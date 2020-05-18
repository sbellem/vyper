from collections import OrderedDict
from typing import Any, Callable, Optional, Sequence, Union

from vyper.compiler import output
from vyper.compiler.phases import CompilerData
from vyper.opcodes import DEFAULT_EVM_VERSION, evm_wrapper
from vyper.typing import (
    ContractCodes,
    InterfaceDict,
    InterfaceImports,
    OutputDict,
    OutputFormats,
)

OUTPUT_FORMATS = {
    # requires vyper_module
    "ast_dict": output.build_ast_dict,
    # requires global_ctx
    "devdoc": output.build_devdoc,
    "userdoc": output.build_userdoc,
    # requires lll_node
    "external_interface": output.build_external_interface_output,
    "interface": output.build_interface_output,
    "ir": output.build_ir_output,
    "method_identifiers": output.build_method_identifiers_output,
    # requires assembly
    "abi": output.build_abi_output,
    "asm": output.build_asm_output,
    "source_map": output.build_source_map_output,
    # requires bytecode
    "bytecode": output.build_bytecode_output,
    "bytecode_runtime": output.build_bytecode_runtime_output,
    "opcodes": output.build_opcodes_output,
    "opcodes_runtime": output.build_opcodes_runtime_output,
}

from mpc.compiler import output as mpc_ouput  # noqa E402

MPC_OUTPUT_FORMATS = {
    # requires mpc_module
    "ast_dict": output.build_ast_dict,
}


@evm_wrapper
def compile_codes(
    contract_sources: ContractCodes,
    output_formats: Union[OutputDict, OutputFormats, None] = None,
    exc_handler: Union[Callable, None] = None,
    interface_codes: Union[InterfaceDict, InterfaceImports, None] = None,
    initial_id: int = 0,
    transformers=None,
) -> OrderedDict:
    """
    Generate compiler output(s) from one or more contract source codes.

    Arguments
    ---------
    contract_sources: Dict[str, str]
        Vyper source codes to be compiled. Formatted as `{"contract name": "source code"}`
    output_formats: List, optional
        List of compiler outputs to generate. Possible options are all the keys
        in `OUTPUT_FORMATS`. If not given, the deployment bytecode is generated.
    exc_handler: Callable, optional
        Callable used to handle exceptions if the compilation fails. Should accept
        two arguments - the name of the contract, and the exception that was raised
    initial_id: int, optional
        The lowest source ID value to be used when generating the source map.
    evm_version: str, optional
        The target EVM ruleset to compile for. If not given, defaults to the latest
        implemented ruleset.
    interface_codes: Dict, optional
        Interfaces that may be imported by the contracts during compilation.

        * May be a singular dictionary shared across all sources to be compiled,
          i.e. `{'interface name': "definition"}`
        * or may be organized according to contracts that are being compiled, i.e.
          `{'contract name': {'interface name': "definition"}`

        * Interface definitions are formatted as: `{'type': "json/vyper", 'code': "interface code"}`
        * JSON interfaces are given as lists, vyper interfaces as strings

    Returns
    -------
    Dict
        Compiler output as `{'contract name': {'output key': "output data"}}`
    """

    if output_formats is None:
        output_formats = ("bytecode",)
    if isinstance(output_formats, Sequence):
        # output_formats = {k: output_formats for k in contract_sources}
        output_formats = dict((k, output_formats) for k in contract_sources.keys())

    out: OrderedDict = OrderedDict()
    for source_id, contract_name in enumerate(
        sorted(contract_sources), start=initial_id
    ):
        # trailing newline fixes python parsing bug when source ends in a comment
        # https://bugs.python.org/issue35107
        source_code = f"{contract_sources[contract_name]}\n"
        _out = get_outputs(
            contract_name,
            source_code,
            output_formats=output_formats[contract_name],
            exc_handler=exc_handler,
            interface_codes=interface_codes,
            source_id=source_id,
        )
        out[contract_name] = _out
        # interfaces: Any = interface_codes
        # if (
        #    isinstance(interfaces, dict)
        #    and contract_name in interfaces
        #    and isinstance(interfaces[contract_name], dict)
        # ):
        #    interfaces = interfaces[contract_name]

        # compiler_data = CompilerData(source_code, contract_name, interfaces, source_id)
        # for output_format in output_formats[contract_name]:
        #    if output_format not in OUTPUT_FORMATS:
        #        raise ValueError(f"Unsupported format type {repr(output_format)}")
        #    try:
        #        out.setdefault(contract_name, {})
        #        out[contract_name][output_format] = OUTPUT_FORMATS[output_format](
        #            compiler_data
        #        )
        #    except Exception as exc:
        #        if exc_handler is not None:
        #            exc_handler(contract_name, exc)
        #        else:
        #            raise exc

    return out


UNKNOWN_CONTRACT_NAME = "<unknown>"


def _compile_code(
    contract_source: str,
    output_formats: Optional[OutputFormats] = None,
    interface_codes: Optional[InterfaceImports] = None,
    evm_version: str = DEFAULT_EVM_VERSION,
) -> dict:
    """
    Generate compiler output(s) from a single contract source code.

    Arguments
    ---------
    contract_source: str
        Vyper source codes to be compiled.
    output_formats: List, optional
        List of compiler outputs to generate. Possible options are all the keys
        in `OUTPUT_FORMATS`. If not given, the deployment bytecode is generated.
    evm_version: str, optional
        The target EVM ruleset to compile for. If not given, defaults to the latest
        implemented ruleset.
    interface_codes: Dict, optional
        Interfaces that may be imported by the contracts during compilation.

        * Formatted as as `{'interface name': {'type': "json/vyper", 'code': "interface code"}}`
        * JSON interfaces are given as lists, vyper interfaces as strings

    Returns
    -------
    Dict
        Compiler output as `{'output key': "output data"}`
    """

    contract_sources = {UNKNOWN_CONTRACT_NAME: contract_source}

    return compile_codes(
        contract_sources,
        output_formats,
        interface_codes=interface_codes,
        evm_version=evm_version,
    )[UNKNOWN_CONTRACT_NAME]


########################################################################################
#                                                                                      #
#                             ratelang experiment                                      #
#                                                                                      #
########################################################################################


def get_outputs(
    contract_name: str,
    source_code: str,
    output_formats: Union[OutputFormats, None] = None,
    exc_handler: Union[Callable, None] = None,
    interface_codes: Union[InterfaceDict, InterfaceImports, None] = None,
    source_id: int = 0,
):
    out = {}
    interfaces: Any = interface_codes
    if (
        isinstance(interfaces, dict)
        and contract_name in interfaces
        and isinstance(interfaces[contract_name], dict)
    ):
        interfaces = interfaces[contract_name]

    compiler_data = CompilerData(source_code, contract_name, interfaces, source_id)
    for output_format in output_formats:
        if output_format not in OUTPUT_FORMATS:
            raise ValueError(f"Unsupported format type {repr(output_format)}")
        try:
            out[output_format] = OUTPUT_FORMATS[output_format](compiler_data)
        except Exception as exc:
            if exc_handler is not None:
                exc_handler(contract_name, exc)
            else:
                raise exc
    return out


@evm_wrapper
def ratel_compile_codes(
    contract_sources: ContractCodes,
    output_formats: Union[OutputDict, OutputFormats, None] = None,
    exc_handler: Union[Callable, None] = None,
    interface_codes: Union[InterfaceDict, InterfaceImports, None] = None,
    initial_id: int = 0,
    ratel_compiler_machine=None,
) -> OrderedDict:
    if output_formats is None:
        output_formats = ("bytecode",)
    if isinstance(output_formats, Sequence):
        output_formats = {
            contract_name: output_formats for contract_name in contract_sources
        }

    out: OrderedDict = OrderedDict()
    for source_id, contract_name in enumerate(
        sorted(contract_sources), start=initial_id
    ):
        # trailing newline fixes python parsing bug when source ends in a comment
        # https://bugs.python.org/issue35107
        source_code = f"{contract_sources[contract_name]}\n"
        _out = get_outputs(
            contract_name,
            source_code,
            output_formats=output_formats[contract_name],
            exc_handler=exc_handler,
            interface_codes=interface_codes,
            source_id=source_id,
        )
        out[contract_name] = _out

    return out


# RATEL: alias for "native" vyper `compile_codes` function
vyper_compile_codes = compile_codes


# def ratel_compile_code(
def compile_code(
    contract_source: str,
    output_formats: Optional[OutputFormats] = None,
    interface_codes: Optional[InterfaceImports] = None,
    evm_version: str = DEFAULT_EVM_VERSION,
    *,
    # external CompilerMachine or CompilerData
    foreign_code_compiler=None,
    foreign_code_output_formats=None,
    return_vyper_source=False,
) -> dict:
    # RATEL
    # process contract source code to extract vyper code, and foreign code
    if foreign_code_compiler:
        fcc = foreign_code_compiler
        vyper_code = fcc.extract_vyper_code(contract_source)
    else:
        vyper_code = contract_source
    # TODO
    # vyper_output = compile_code(
    #    vyper_code, output_formats, interface_codes, evm_version
    # )
    # foreign_output = ...
    # return {"vyper": vyper_output, "foreign_code_key": foreign_output}
    vyper_contract_sources = {UNKNOWN_CONTRACT_NAME: vyper_code}
    output = vyper_compile_codes(
        vyper_contract_sources,
        output_formats,
        interface_codes=interface_codes,
        evm_version=evm_version,
    )[UNKNOWN_CONTRACT_NAME]
    if return_vyper_source:
        output = (output, vyper_code)
    return output

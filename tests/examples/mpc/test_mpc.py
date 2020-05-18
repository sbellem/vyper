import pytest

from vyper import compiler

INITIAL_VALUE = 4


def _get_contract(w3, source_code, *args, **kwargs):
    from tests.base_conftest import VyperContract
    from tests.grammar.conftest import get_lark_grammar

    LARK_GRAMMAR = get_lark_grammar()
    return_vyper_source = kwargs.pop("return_vyper_source", False)

    out = compiler.compile_code(
        source_code,
        ["abi", "bytecode"],
        interface_codes=kwargs.pop("interface_codes", None),
        evm_version=kwargs.pop("evm_version", None),
        foreign_code_compiler=kwargs.pop("foreign_code_compiler", None),
        return_vyper_source=return_vyper_source,
    )

    if return_vyper_source:
        out, vyper_source = out
    else:
        vyper_source = source_code

    LARK_GRAMMAR.parse(vyper_source + "\n")  # Test grammar.
    abi = out["abi"]
    bytecode = out["bytecode"]
    value = (
        kwargs.pop("value_in_eth", 0) * 10 ** 18
    )  # Handle deploying with an eth value.
    c = w3.eth.contract(abi=abi, bytecode=bytecode)
    deploy_transaction = c.constructor(*args)
    tx_info = {
        "from": w3.eth.accounts[0],
        "value": value,
        "gasPrice": 0,
    }
    tx_info.update(kwargs)
    tx_hash = deploy_transaction.transact(tx_info)
    address = w3.eth.getTransactionReceipt(tx_hash)["contractAddress"]
    contract = w3.eth.contract(
        address, abi=abi, bytecode=bytecode, ContractFactoryClass=VyperContract,
    )
    return contract


@pytest.fixture
def get_contract(w3):
    def get_contract(source_code, *args, **kwargs):
        return _get_contract(w3, source_code, *args, **kwargs)

    return get_contract


@pytest.fixture
def mpc_contract_code():
    with open("examples/mpc/mpc.vy") as f:
        contract_code = f.read()
    return contract_code


@pytest.fixture
def mpc_contract(w3, get_contract, mpc_contract_code):
    from mpc.compiler.machine import RatelCompiler

    foreign_code_compiler = RatelCompiler()
    contract = get_contract(
        mpc_contract_code,
        INITIAL_VALUE,
        foreign_code_compiler=foreign_code_compiler,
        return_vyper_source=True,
    )
    return contract


def test_initial_state(mpc_contract):
    # Check if the constructor of the contract is set up properly
    assert mpc_contract.storedData() == INITIAL_VALUE


@pytest.mark.skip
def test_compile(mpc_contract_code):
    from vyper import compiler

    compiler_output = compiler.compile_code(
        mpc_contract_code,
        output_formats=["abi", "bytecode", "mpc"],
        interface_codes=None,
        evm_version=None,
    )
    assert compiler_output

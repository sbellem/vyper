import pytest

INITIAL_VALUE = 4


# NOTE Taken and adapted from vyperlang/vyper.
def _get_contract(w3, source_code, *args, **kwargs):
    from tests.base_conftest import VyperContract
    from tests.grammar.conftest import get_lark_grammar
    from ratel import RatelCompiler

    LARK_GRAMMAR = get_lark_grammar()

    ratel_compiler = RatelCompiler()
    out = ratel_compiler.compile(
        source_code,
        vyper_output_formats=["abi", "bytecode"],
        vyper_interface_codes=kwargs.pop("interface_codes", None),
        evm_version=kwargs.pop("evm_version", None),
        mpc_output_formats=kwargs.pop("mpc_output_formats", None),
    )

    vyper_source = ratel_compiler._vyper_code
    LARK_GRAMMAR.parse(vyper_source + "\n")  # Test grammar.

    vyper_output = out["vyper"]
    abi = vyper_output["abi"]
    bytecode = vyper_output["bytecode"]
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
    contract = get_contract(mpc_contract_code, INITIAL_VALUE,)
    return contract


def test_initial_state(mpc_contract):
    # Check if the constructor of the contract is set up properly
    assert mpc_contract.storedData() == INITIAL_VALUE


def test_compile(mpc_contract_code):
    from tests.grammar.conftest import get_lark_grammar
    from ratel import RatelCompiler

    LARK_GRAMMAR = get_lark_grammar()

    ratel_compiler = RatelCompiler()
    out = ratel_compiler.compile(
        mpc_contract_code, vyper_output_formats=["abi", "bytecode"],
    )

    vyper_source = ratel_compiler._vyper_code
    LARK_GRAMMAR.parse(vyper_source + "\n")  # Test grammar.
    mpc_output = out["mpc"]
    mpc_src_code = mpc_output["src_code"]
    exec(mpc_src_code, globals())
    assert multiply(3, 4) == 12  # noqa F821

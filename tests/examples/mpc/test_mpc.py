import pytest

INITIAL_VALUE = 4


@pytest.fixture
def mpc_contract_code():
    with open("examples/mpc/mpc.vy") as f:
        contract_code = f.read()
    return contract_code


@pytest.fixture
def mpc_contract(w3, get_contract, contract_code):
    contract = get_contract(contract_code, INITIAL_VALUE)
    return contract


def test_initial_state(mpc_contract):
    # Check if the constructor of the contract is set up properly
    assert mpc_contract.storedData() == INITIAL_VALUE


def test_compile(mpc_contract_code):
    from vyper import compiler

    compiler_output = compiler.compile(
        mpc_contract_code,
        output_formats=["abi", "bytecode", "mpc"],
        interface_codes=None,
        evm_version=None,
    )

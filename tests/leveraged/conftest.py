import pytest
from brownie import Contract, accounts, Wei


@pytest.fixture
def comp():
    yield Contract("0xAB1c342C7bf5Ec5F02ADEA1c2270670bCa144CbB")


@pytest.fixture
def compAdmin(comp):
    yield accounts.at(comp.admin(), force=True)


@pytest.fixture
def vault():
    yield Contract("0x6392e8fa0588CB2DCb7aF557FdC9D10FDe48A325")


@pytest.fixture
def gov(vault):
    yield accounts.at(vault.governance(), force=True)


@pytest.fixture
def leverager(gov, vault, comp, compAdmin, LeveragedEthStrategy):
    leverager = gov.deploy(LeveragedEthStrategy, vault)
    # Ask for around 100 eth credit is in USD
    comp._setCreditLimit(leverager, 600 * Wei("100 ether"), {"from": compAdmin})
    vault.addStrategy(leverager, Wei("200 ether"), 0, 0, {"from": gov})
    yield leverager


@pytest.fixture
def strategy(leverager, gov, HomoraStrategy):
    strategy = gov.deploy(HomoraStrategy, leverager)
    leverager.setInnerStrategy(strategy, {"from": gov})
    yield strategy


@pytest.fixture
def weth():
    yield Contract("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")


@pytest.fixture
def whale(weth):
    whale = accounts[1]
    weth.deposit({"from": whale, "value": whale.balance()})
    yield whale

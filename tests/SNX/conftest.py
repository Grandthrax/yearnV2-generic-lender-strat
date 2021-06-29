import pytest
from brownie import Wei, config, Contract


@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


@pytest.fixture
def guardian(accounts):
    # YFI Whale, probably
    yield accounts[2]


@pytest.fixture
def keeper(accounts):
    # This is our trusty bot!
    yield accounts[4]


@pytest.fixture
def rando(accounts):
    yield accounts[9]


@pytest.fixture
def snx_whale(accounts):
    yield accounts.at("0x1494ca1f11d487c2bbe4543e90080aeba4ba3c2b", force=True)


@pytest.fixture
def snx():
    yield Contract("0xc011a73ee8576fb46f5e1c5751ca3b9fe0af2a6f")


@pytest.fixture
def cySNX(interface):
    yield interface.CErc20I("0x12A9cC33A980DAa74E00cc2d1A0E74C57A93d12C")


@pytest.fixture
def vault():
    yield Contract("0xF29AE508698bDeF169B89834F76704C3B205aedf")


@pytest.fixture
def strategy(strategist, keeper, vault, Strategy, GenericCream, cySNX):
    gov = vault.governance()
    strategy = strategist.deploy(Strategy, vault)
    strategy.setKeeper(keeper)

    creamPlugin = strategist.deploy(GenericCream, strategy, "IB", cySNX)
    strategy.addLender(creamPlugin, {"from": gov})

    assert strategy.numLenders() == 1

    yield strategy

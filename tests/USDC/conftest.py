import pytest
from brownie import Wei, config, Contract


@pytest.fixture
def live_strat_usdc_1(Strategy):
    yield Strategy.at("0xB7e9Bf9De45E1df822E97cA7E0C3D1B62798a4e0")


@pytest.fixture
def live_vault_usdc(pm):
    Vault = pm(config["dependencies"][0]).Vault
    yield Vault.at("0xD6b53d0f3d4e55fbAaADc140C0B0488293a433f8")

@pytest.fixture
def live_vault_usdt(pm):
    Vault = pm(config["dependencies"][0]).Vault
    vault = Vault.at('0xAf322a2eDf31490250fdEb0D712621484b09aBB6')
    yield vault


@pytest.fixture
def live_GenericCompound_usdc_1(GenericCompound):
    yield GenericCompound.at("0x33D4c129586562adfd993ebb54E830481F31ef37")


@pytest.fixture
def live_GenericCream_usdc_1(GenericCream):
    yield GenericCream.at("0x1bAaCef951d24c5d70a8cA88D89cE16B37472fB3")


@pytest.fixture
def live_GenericDyDx_usdc_1(GenericDyDx):
    yield GenericDyDx.at("0x6C842746F21Ca34542EDC6895dFfc8D4e7D2bC1c")

# change these fixtures for generic tests
@pytest.fixture
def currency(dai, usdc, weth):
    yield usdc


@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


@pytest.fixture
def whale(accounts, web3, weth):
    # big binance7 wallet
    # acc = accounts.at('0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8', force=True)
    # big binance8 wallet
    acc = accounts.at("0xf977814e90da44bfa03b6295a0616a897441acec", force=True)

    # lots of weth account
    wethAcc = accounts.at("0x767Ecb395def19Ab8d1b2FCc89B3DDfBeD28fD6b", force=True)
    weth.approve(acc, 2 ** 256 - 1, {"from": wethAcc})
    weth.transfer(acc, weth.balanceOf(wethAcc), {"from": wethAcc})

    assert weth.balanceOf(acc) > 0
    yield acc


@pytest.fixture()
def strategist(accounts, whale, currency):
    decimals = currency.decimals()
    currency.transfer(accounts[1], 100_000 * (10 ** decimals), {"from": whale})
    yield accounts[1]


@pytest.fixture
def samdev(accounts):
    yield accounts.at("0xC3D6880fD95E06C816cB030fAc45b3ffe3651Cb0", force=True)


@pytest.fixture
def gov(accounts):
    yield accounts[3]


@pytest.fixture
def rewards(gov):
    yield gov  # TODO: Add rewards contract


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


# specific addresses
@pytest.fixture
def usdc(interface):
    yield interface.ERC20("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")


@pytest.fixture
def dai(interface):
    yield interface.ERC20("0x6b175474e89094c44da98b954eedeac495271d0f")


@pytest.fixture
def weth(interface):
    yield interface.IWETH("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")


@pytest.fixture
def cdai(interface):
    yield interface.CErc20I("0x5d3a536e4d6dbd6114cc1ead35777bab948e3643")


@pytest.fixture
def cUsdc(interface):
    yield interface.CErc20I("0x39AA39c021dfbaE8faC545936693aC917d5E7563")


@pytest.fixture
def crUsdc(interface):
    yield interface.CErc20I("0x44fbeBd2F576670a6C33f6Fc0B00aA8c5753b322")


@pytest.fixture
def aUsdc(interface):
    yield interface.IAToken("0xBcca60bB61934080951369a648Fb03DF4F96263C")


@pytest.fixture(scope="module", autouse=True)
def shared_setup(module_isolation):
    pass


@pytest.fixture
def vault(gov, rewards, guardian, currency, pm):
    Vault = pm(config["dependencies"][0]).Vault
    vault = Vault.deploy({"from": guardian})
    vault.initialize(currency, gov, rewards, "", "")
    vault.setManagementFee(0, {"from": gov})
    yield vault


@pytest.fixture
def strategy(
    strategist,
    gov,
    rewards,
    keeper,
    vault,
    crUsdc,
    cUsdc,
    aUsdc,
    Strategy,
    GenericCompound,
    GenericCream,
    GenericDyDx,
    GenericAave,
    chain
):
    strategy = strategist.deploy(Strategy, vault)
    strategy.setKeeper(keeper, {"from": gov})
    strategy.setWithdrawalThreshold(0, {"from": gov})
    strategy.setRewards(rewards, {"from": strategist})

    compoundPlugin = strategist.deploy(GenericCompound, strategy, "Compound", cUsdc)
    creamPlugin = strategist.deploy(GenericCream, strategy, "Cream", crUsdc)
    dydxPlugin = strategist.deploy(GenericDyDx, strategy, "DyDx")
    aavePlugin = strategist.deploy(GenericAave, strategy, "Aave", aUsdc, False)

    strategy.addLender(creamPlugin, {"from": gov})
    assert strategy.numLenders() == 1
    strategy.addLender(compoundPlugin, {"from": gov})
    assert strategy.numLenders() == 2
    strategy.addLender(dydxPlugin, {"from": gov})
    assert strategy.numLenders() == 3
    strategy.addLender(aavePlugin, {"from": gov})
    assert strategy.numLenders() == 4

    yield strategy

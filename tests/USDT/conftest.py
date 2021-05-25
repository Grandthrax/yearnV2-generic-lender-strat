import pytest
from brownie import Wei, config


@pytest.fixture
def live_strat_usdc_1(Strategy):
    yield Strategy.at("0xB7e9Bf9De45E1df822E97cA7E0C3D1B62798a4e0")

@pytest.fixture
def live_strat_weth_1(Strategy):
    yield Strategy.at("0xeE697232DF2226c9fB3F02a57062c4208f287851")

@pytest.fixture
def live_strat_usdt_1(Strategy):
    yield Strategy.at("0x660F73c3C45ca124084a676D3635e5b015E99941")

@pytest.fixture
def live_vault_usdc(pm):
    Vault = pm(config["dependencies"][0]).Vault
    yield Vault.at("0xD6b53d0f3d4e55fbAaADc140C0B0488293a433f8")

@pytest.fixture
def live_vault_usdt(pm):
    Vault = pm(config["dependencies"][0]).Vault
    vault = Vault.at('0x7Da96a3891Add058AdA2E826306D812C638D87a7')
    yield vault


@pytest.fixture
def live_GenericCompound_usdc_1(GenericCompound):
    yield GenericCompound.at("0x33D4c129586562adfd993ebb54E830481F31ef37")


@pytest.fixture
def live_GenericCream_usdc_1(GenericCream):
    yield GenericCream.at("0x1bAaCef951d24c5d70a8cA88D89cE16B37472fB3")

@pytest.fixture
def live_GenericCream_aave_1(GenericCream):
    yield GenericCream.at("0x2c1a28FB72dC1db8d7010009b234580feD13e944")
    
@pytest.fixture
def live_GenericCream_usdt_1(GenericCream):
    yield GenericCream.at("0xe18a775De318aa1274116036a9bB0Fe554Ab23D4")

@pytest.fixture
def live_GenericDyDx_usdc_1(GenericDyDx):
    yield GenericDyDx.at("0x6C842746F21Ca34542EDC6895dFfc8D4e7D2bC1c")


# change these fixtures for generic tests
@pytest.fixture
def currency(dai, usdt, weth):
    yield usdt

@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


@pytest.fixture
def whale(accounts, web3, weth):
    # big binance7 wallet
    #acc = accounts.at('0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8', force=True)
    # big binance8 wallet
    acc = accounts.at("0xA929022c9107643515F5c777cE9a910F0D1e490C", force=True)

    # lots of weth account
    wethAcc = accounts.at("0x767Ecb395def19Ab8d1b2FCc89B3DDfBeD28fD6b", force=True)
    weth.approve(acc, 2 ** 256 - 1, {"from": wethAcc})
    weth.transfer(acc, weth.balanceOf(wethAcc), {"from": wethAcc})

    assert weth.balanceOf(acc) > 0
    yield acc


@pytest.fixture()
def strategist(accounts, whale, currency):
    decimals = currency.decimals()
    usdt_whale = "0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503"
    currency.transfer(accounts[1], 100_000 * (10 ** decimals), {"from": usdt_whale})
    yield accounts[1]


@pytest.fixture
def samdev(accounts, whale, currency):
    st = accounts.at("0xC3D6880fD95E06C816cB030fAc45b3ffe3651Cb0", force=True)
    decimals = currency.decimals()
    currency.transfer(st, 100_000 * (10 ** decimals), {"from": whale})
    yield st

@pytest.fixture
def stratms(accounts):
    yield accounts.at("0x16388463d60FFE0661Cf7F1f31a7D658aC790ff7", force=True)


@pytest.fixture
def gov(accounts):
    yield accounts[3]

@pytest.fixture
def daddy(accounts):
    yield accounts.at("0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52", force=True)

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
def usdt(interface):
    yield interface.ERC20("0xdAC17F958D2ee523a2206206994597C13D831ec7")


@pytest.fixture
def dai(interface):
    yield interface.ERC20("0x6b175474e89094c44da98b954eedeac495271d0f")


@pytest.fixture
def weth(interface):
    yield interface.IWETH("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")

@pytest.fixture
def cUsdt(interface):
    yield interface.CErc20I("0xf650C3d88D12dB855b8bf7D11Be6C55A4e07dCC9")


@pytest.fixture
def crUsdt(interface):
    yield interface.CErc20I("0x797AAB1ce7c01eB727ab980762bA88e7133d2157")


@pytest.fixture
def aUsdt(interface):
    yield interface.IAToken("0x3Ed3B47Dd13EC9a98b44e6204A523E766B225811")


@pytest.fixture(scope="module", autouse=True)
def shared_setup(module_isolation):
    pass


@pytest.fixture
def vault(gov, rewards, guardian, currency, pm, live_vault_usdt, stratms, daddy):
    Vault = pm(config["dependencies"][0]).Vault
    vault = Vault.deploy({"from": guardian})
    vault.initialize(currency, gov, rewards, "", "")
    vault.setManagementFee(0, {"from": gov})
    #yield vault
    #vault = live_vault_usdt
    #vault.setGovernance(daddy, {'from': stratms})
    #vault.acceptGovernance({'from': daddy})

    yield vault


@pytest.fixture
def strategy(
    strategist,
    live_strat_weth_1,
    daddy,
    rewards,
    keeper,
    currency,
    vault,
    crUsdt,
    cUsdt,
    Strategy,
    live_strat_usdt_1,
    live_GenericCream_aave_1,
    live_GenericCream_usdt_1,
    aUsdt,
    GenericCompound,
    GenericCream,
    GenericAave,
    accounts
):
    gov = accounts.at(vault.governance(), force=True)
    tx = live_strat_weth_1.clone(vault, {"from": strategist})
    strategy = Strategy.at(tx.return_value)
    #strategy = live_strat_usdt_1
    strategist = accounts.at(strategy.strategist(), force=True)
    strategy.setRewards(strategist, {"from": strategist})
    strategy.setWithdrawalThreshold(0, {"from": strategist})

    compoundPlugin = strategist.deploy(GenericCompound, strategy, "Compound", cUsdt)

    #tx = live_GenericCream_aave_1.cloneCreamLender(strategy,"Cream", crUsdt, {"from": strategist})
    #creamPlugin = GenericCream.at(tx.return_value)
    #creamPlugin = live_GenericCream_usdt_1
    creamPlugin = strategist.deploy(GenericCream, strategy, "Cream", crUsdt)

    aavePlugin = strategist.deploy(GenericAave, strategy, "Aave", aUsdt, True)

    strategy.addLender(creamPlugin, {"from": gov})
    assert strategy.numLenders() == 1
    strategy.addLender(compoundPlugin, {"from": gov})
    assert strategy.numLenders() == 2
    strategy.addLender(aavePlugin, {"from": gov})
    assert strategy.numLenders() == 3

    strategy.setDebtThreshold(1*1e6, {"from": gov})
    strategy.setProfitFactor(1500, {"from": gov})
    strategy.setMaxReportDelay(86000, {"from": gov})

    yield strategy

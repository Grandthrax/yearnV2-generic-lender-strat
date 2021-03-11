from itertools import count
from brownie import Wei, reverts
from useful_methods import genericStateOfVault, genericStateOfStrat
import random
import brownie


def test_apr_weth(
    weth,
    Strategy,
    chain,
    rewards,
    whale,
    gov,
    strategist,
    rando,
    Vault,
    interface,
    AlphaHomo,
    EthCream,
    EthCompound,
):
    crETH = interface.CEtherI("0xD06527D5e56A3495252A528C4987003b712860eE")
    vault = Vault.deploy({"from": gov})
    vault.initialize(weth, gov, rewards, "", "")
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})

    weth.approve(vault, 2 ** 256 - 1, {"from": whale})

    strategy = strategist.deploy(Strategy, vault)

    ethCreamPlugin = strategist.deploy(EthCream, strategy, "Cream")
    strategy.addLender(ethCreamPlugin, {"from": gov})

    compoundPlugin = strategist.deploy(EthCompound, strategy, "Compound")
    strategy.addLender(compoundPlugin, {"from": gov})

    # assert strategy.numLenders() == 2

    deposit_limit = 10_000
    vault.addStrategy(strategy, deposit_limit, 0, 2 ** 256 - 1, 1000, {"from": gov})

    whale_deposit = 1000 * 1e18
    vault.deposit(whale_deposit, {"from": whale})
    chain.sleep(10)
    chain.mine(1)
    strategy.setWithdrawalThreshold(0, {"from": gov})
    assert strategy.harvestTrigger(1 * 1e18) == True
    print(whale_deposit / 1e18)
    print(ethCreamPlugin.aprAfterDeposit(0) / 1e18)
    print(compoundPlugin.aprAfterDeposit(0) / 1e18)

    strategy.harvest({"from": strategist})
    startingBalance = vault.totalAssets()
    for i in range(2):

        waitBlock = 25
        # print(f'\n----wait {waitBlock} blocks----')
        chain.mine(waitBlock)
        chain.sleep(waitBlock * 13)
        # print(f'\n----harvest----')
        crETH.mint({"from": whale})
        strategy.harvest({"from": strategist})

        # genericStateOfStrat(strategy, currency, vault)
        # genericStateOfVault(vault, currency)

        profit = (vault.totalAssets() - startingBalance) / 1e6
        strState = vault.strategies(strategy)
        totalReturns = strState[7]
        totaleth = totalReturns / 1e6
        # print(f'Real Profit: {profit:.5f}')
        difff = profit - totaleth
        # print(f'Diff: {difff}')

        blocks_per_year = 2_252_857
        assert startingBalance != 0
        time = (i + 1) * waitBlock
        assert time != 0
        apr = (totalReturns / startingBalance) * (blocks_per_year / time)
        assert apr > 0 and apr < 1
        # print(apr)
        print(f"implied apr: {apr:.8%}")

    vault.withdraw(vault.balanceOf(whale), {"from": whale})

    vBal = vault.balanceOf(strategy)
    assert vBal > 0
    print(vBal)
    vBefore = vault.balanceOf(strategist)
    vault.transferFrom(strategy, strategist, vBal, {"from": strategist})
    print(vault.balanceOf(strategist) - vBefore)
    assert vault.balanceOf(strategist) - vBefore > 0


def test_tend_trigger_weth(
    weth,
    Strategy,
    chain,
    rewards,
    whale,
    gov,
    strategist,
    rando,
    Vault,
    AlphaHomo,
    interface,
    EthCream,
    EthCompound,
):
    crETH = interface.CEtherI("0xD06527D5e56A3495252A528C4987003b712860eE")
    cETH = interface.CEtherI("0x4Ddc2D193948926D02f9B1fE9e1daa0718270ED5")
    bank = interface.Bank("0x67B66C99D3Eb37Fa76Aa3Ed1ff33E8e39F0b9c7A")

    vault = Vault.deploy({"from": gov})
    vault.initialize(weth, gov, rewards, "", "")
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})

    weth.approve(vault, 2 ** 256 - 1, {"from": whale})

    strategy = strategist.deploy(Strategy, vault)

    ethCreamPlugin = strategist.deploy(EthCream, strategy, "Cream")
    strategy.addLender(ethCreamPlugin, {"from": gov})

    alphaHomoPlugin = strategist.deploy(AlphaHomo, strategy, "Alpha Homo")
    strategy.addLender(alphaHomoPlugin, {"from": gov})

    compoundPlugin = strategist.deploy(EthCompound, strategy, "Compound")
    strategy.addLender(compoundPlugin, {"from": gov})
    strategy.setWithdrawalThreshold(0, {"from": gov})
    assert strategy.numLenders() == 3

    deposit_limit = 100_000_000 * 1e18
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 500, {"from": gov})
    vault.setDepositLimit(deposit_limit, {"from": gov})

    whale_deposit = 1_000 * 1e18
    vault.deposit(whale_deposit, {"from": whale})

    weth.withdraw(weth.balanceOf(whale), {"from": whale})
    balance = whale.balance() - 1e18  # leave 1 eth for gas
    crETH.mint({"from": whale, "value": balance})

    chain.sleep(10)
    chain.mine(1)
    assert strategy.harvestTrigger(1 * 1e18) == True
    strategy.harvest({"from": strategist})
    form = "{:.2%}"
    formS = "{:,.0f}"
    status = strategy.lendStatuses()
    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
        )
    chain.sleep(10)
    chain.mine(1)
    # should be no change
    assert strategy.tendTrigger(0) == False
    crETH.redeem(crETH.balanceOf(whale), {"from": whale})
    bank.deposit({"from": whale, "value": balance})
    chain.sleep(10)
    chain.mine(1)
    status = strategy.lendStatuses()
    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
        )
    assert strategy.tendTrigger(1 * 1e18) == False
    assert strategy.tendTrigger(1e14) == True
    status = strategy.lendStatuses()
    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
        )
    strategy.tend({"from": strategist})
    status = strategy.lendStatuses()
    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
        )


def test_debt_increase_weth(
    weth,
    Strategy,
    chain,
    rewards,
    whale,
    gov,
    strategist,
    rando,
    Vault,
    GenericDyDx,
    AlphaHomo,
    interface,
    EthCream,
    EthCompound,
):

    currency = weth

    crETH = interface.CEtherI("0xD06527D5e56A3495252A528C4987003b712860eE")
    cETH = interface.CEtherI("0x4Ddc2D193948926D02f9B1fE9e1daa0718270ED5")

    vault = Vault.deploy({"from": gov})
    vault.initialize(weth, gov, rewards, "", "")
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})

    weth.approve(vault, 2 ** 256 - 1, {"from": whale})

    strategy = strategist.deploy(Strategy, vault)

    ethCreamPlugin = strategist.deploy(EthCream, strategy, "Cream")
    strategy.addLender(ethCreamPlugin, {"from": gov})

    alphaHomoPlugin = strategist.deploy(AlphaHomo, strategy, "Alpha Homo")
    strategy.addLender(alphaHomoPlugin, {"from": gov})

    compoundPlugin = strategist.deploy(EthCompound, strategy, "Compound")
    strategy.addLender(compoundPlugin, {"from": gov})

    dydxPlugin = strategist.deploy(GenericDyDx, strategy, "DyDx")
    strategy.addLender(dydxPlugin, {"from": gov})
    assert strategy.numLenders() == 4

    strategy.setWithdrawalThreshold(0, {"from": gov})

    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 500, {"from": gov})

    form = "{:.2%}"
    formS = "{:,.0f}"
    firstDeposit = 1_000 * 1e18
    predictedApr = strategy.estimatedFutureAPR(firstDeposit)
    print(
        f"Predicted APR from {formS.format(firstDeposit/1e18)} deposit: {form.format(predictedApr/1e18)}"
    )
    vault.deposit(firstDeposit, {"from": whale})

    print("Deposit: ", formS.format(firstDeposit / 1e18))
    strategy.harvest({"from": strategist})
    realApr = strategy.estimatedAPR()
    print("Current APR: ", form.format(realApr / 1e18))
    status = strategy.lendStatuses()

    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
        )

    assert realApr > predictedApr * 0.999 and realApr < predictedApr * 1.001

    predictedApr = strategy.estimatedFutureAPR(firstDeposit * 2)
    print(
        f"\nPredicted APR from {formS.format(firstDeposit/1e18)} deposit: {form.format(predictedApr/1e18)}"
    )
    print("Deposit: ", formS.format(firstDeposit / 1e18))
    vault.deposit(firstDeposit, {"from": whale})

    strategy.harvest({"from": strategist})
    realApr = strategy.estimatedAPR()

    print(f"Real APR after deposit: {form.format(realApr/1e18)}")
    status = strategy.lendStatuses()

    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
        )
    assert realApr > predictedApr * 0.999 and realApr < predictedApr * 1.001


def test_debt_increment_weth(
    weth,
    Strategy,
    chain,
    rewards,
    whale,
    gov,
    strategist,
    rando,
    Vault,
    GenericDyDx,
    AlphaHomo,
    interface,
    EthCream,
    EthCompound,
):

    currency = weth

    crETH = interface.CEtherI("0xD06527D5e56A3495252A528C4987003b712860eE")
    cETH = interface.CEtherI("0x4Ddc2D193948926D02f9B1fE9e1daa0718270ED5")
    bank = interface.Bank("0x67B66C99D3Eb37Fa76Aa3Ed1ff33E8e39F0b9c7A")
    balance = whale.balance() - 1e18  # leave 1 eth for gas

    vault = Vault.deploy({"from": gov})
    vault.initialize(weth, gov, rewards, "", "")
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})

    weth.approve(vault, 2 ** 256 - 1, {"from": whale})
    weth.deposit({"from": whale, "value": balance})

    strategy = strategist.deploy(Strategy, vault)

    ethCreamPlugin = strategist.deploy(EthCream, strategy, "Cream")
    strategy.addLender(ethCreamPlugin, {"from": gov})

    alphaHomoPlugin = strategist.deploy(AlphaHomo, strategy, "Alpha Homo")
    strategy.addLender(alphaHomoPlugin, {"from": gov})

    compoundPlugin = strategist.deploy(EthCompound, strategy, "Compound")
    strategy.addLender(compoundPlugin, {"from": gov})

    dydxPlugin = strategist.deploy(GenericDyDx, strategy, "DyDx")
    strategy.addLender(dydxPlugin, {"from": gov})

    assert strategy.numLenders() == 4

    deposit_limit = 10_000
    vault.addStrategy(strategy, deposit_limit, 0, 2 ** 256 - 1, 1000, {"from": gov})

    form = "{:.2%}"
    formS = "{:,.0f}"
    for i in range(10):
        firstDeposit = 3000 * 1e18

        vault.deposit(firstDeposit, {"from": whale})
        print("\nDeposit: ", formS.format(firstDeposit / 1e18))
        strategy.harvest({"from": strategist})
        realApr = strategy.estimatedAPR()
        print("Current APR: ", form.format(realApr / 1e18))
        status = strategy.lendStatuses()

        for j in status:
            print(
                f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
            )

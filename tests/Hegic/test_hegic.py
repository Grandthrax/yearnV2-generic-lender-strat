from itertools import count
from brownie import Wei, reverts
from useful_methods import genericStateOfVault, genericStateOfStrat
import random
import brownie


def test_normal_hegic(
    hegic, crHegic, chain, whale, gov, strategist, rando, vault, strategy, fn_isolation,
):

    currency = hegic
    starting_balance = currency.balanceOf(strategist)

    decimals = currency.decimals()

    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    currency.approve(vault, 2 ** 256 - 1, {"from": strategist})

    deposit_limit = 1_000_000_000 * (10 ** (decimals))
    vault.setDepositLimit(deposit_limit, {"from": gov})
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 500, {"from": gov})

    # our humble strategist deposits some test funds
    depositAmount = 501 * (10 ** (decimals))
    vault.deposit(depositAmount, {"from": strategist})

    assert strategy.estimatedTotalAssets() == 0
    chain.mine(1)

    assert strategy.harvestTrigger(1) == True

    strategy.harvest({"from": strategist})

    assert (
        strategy.estimatedTotalAssets() >= depositAmount * 0.999999
    )  # losing some dust is ok

    # this fails
    assert strategy.harvestTrigger(1) == False

    # whale deposits as well
    whale_deposit = 100_000 * (10 ** (decimals))
    vault.deposit(whale_deposit, {"from": whale})
    assert strategy.harvestTrigger(1000) == True
    strategy.harvest({"from": strategist})

    for i in range(15):
        waitBlock = random.randint(10, 50)
        crHegic.mint(0, {"from": whale})
        chain.sleep(15 * 30)
        chain.mine(waitBlock)

        strategy.harvest({"from": strategist})
        something = True
        action = random.randint(0, 9)
        if action < 3:
            percent = random.randint(50, 100)

            shareprice = vault.pricePerShare()

            shares = vault.balanceOf(whale)
            print("whale has:", shares / 1e18)
            sharesout = shares * percent / 100
            expectedout = (sharesout * shareprice) / (10 ** (decimals))
            balanceBefore = currency.balanceOf(whale)

            vault.withdraw(sharesout, {"from": whale})
            chain.mine(waitBlock)
            balanceAfter = currency.balanceOf(whale)
            withdrawn = balanceAfter - balanceBefore
            assert withdrawn > expectedout * 0.99 and withdrawn < expectedout * 1.01

        elif action < 5:
            depositAm = random.randint(10, 100) * (10 ** decimals)
            vault.deposit(depositAm, {"from": whale})

    # strategist withdraws
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    shareprice = vault.pricePerShare()

    shares = vault.balanceOf(strategist)
    expectedout = (shares * shareprice) / (10 ** (decimals))
    balanceBefore = currency.balanceOf(strategist)
    print(balanceBefore)
    status = strategy.lendStatuses()
    form = "{:.2%}"
    formS = "{:,.0f}"
    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
        )
    vault.withdraw(vault.balanceOf(strategist), {"from": strategist})
    balanceAfter = currency.balanceOf(strategist)
    print("shares", vault.balanceOf(strategist) / 1e18)
    print(balanceAfter / 1e18)
    status = strategy.lendStatuses()

    chain.mine(waitBlock)
    withdrawn = balanceAfter - balanceBefore
    assert withdrawn > expectedout * 0.99 and withdrawn < expectedout * 1.01

    profit = balanceAfter - starting_balance
    assert profit > 0
    print(profit)


def test_apr_hegic(
    weth,
    strategy,
    crUsdc,
    crComptroller,
    usdc,
    crHegic,
    vault,
    hegic,
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

    deposit_limit = 1_000_000_000 * 1e18
    vault.setDepositLimit(deposit_limit, {"from": gov})
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 500, {"from": gov})
    hegic.approve(vault, 2 ** 256 - 1, {"from": whale})

    whale_deposit = 1_000_000 * 1e18
    vault.deposit(whale_deposit, {"from": whale})
    chain.sleep(10)
    chain.mine(1)
    assert strategy.harvestTrigger(1 * 1e18) == True
    print(whale_deposit / 1e18)

    ##someone borrows:
    crComptroller.enterMarkets([crHegic, crUsdc], {"from": whale})
    hegic.approve(crHegic, 2 ** 256 - 1, {"from": whale})
    usdc.approve(crUsdc, 2 ** 256 - 1, {"from": whale})
    crUsdc.mint(1000_000 * 1e6, {"from": whale})

    whalbal = hegic.balanceOf(whale)
    crHegic.mint(10_000_000 * 1e18, {"from": whale})
    assert hegic.balanceOf(crHegic) > 0
    print("aft: ", (hegic.balanceOf(whale) - whalbal) / 1e18)
    chain.mine(1)
    whalbal = hegic.balanceOf(whale)
    crHegic.borrow(1_000_000 * 1e18, {"from": whale})
    assert hegic.balanceOf(whale) > whalbal
    print("aft: ", (hegic.balanceOf(whale) - whalbal) / 1e18)

    strategy.harvest({"from": strategist})
    startingBalance = vault.totalAssets()
    for i in range(10):
        crHegic.mint(0, {"from": whale})
        waitBlock = 25
        chain.mine(waitBlock)
        chain.sleep(waitBlock * 13)
        strategy.harvest({"from": strategist})

        profit = (vault.totalAssets() - startingBalance) / 1e6
        strState = vault.strategies(strategy)
        totalReturns = strState[6]
        totaleth = totalReturns / 1e6
        difff = profit - totaleth

        blocks_per_year = 2_252_857
        assert startingBalance != 0
        time = (i + 1) * waitBlock
        assert time != 0
        apr = (totalReturns / startingBalance) * (blocks_per_year / time)

        status = strategy.lendStatuses()
        form = "{:.2%}"
        formS = "{:,.0f}"
        for j in status:
            print(
                f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
            )
        print(f"implied apr: {apr:.8%}")

    vault.withdraw(vault.balanceOf(whale), {"from": whale})

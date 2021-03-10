from itertools import count
from brownie import Wei, reverts
from useful_methods import genericStateOfVault, genericStateOfStrat
import random
import brownie


def xtest_clone(
    chain,
    whale,
    gov,
    strategist,
    vault,
    Strategy,
    strategy,
    hegic,
    GenericCream,
    crHegic,
):

    currency = hegic
    starting_balance = currency.balanceOf(strategist)
    decimals = currency.decimals()

    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    currency.approve(vault, 2 ** 256 - 1, {"from": strategist})

    deposit_limit = 1_000_000_000 * (10 ** (decimals))
    vault.setDepositLimit(deposit_limit, {"from": gov})

    # our humble strategist deposits some test funds
    depositAmount = 501 * (10 ** (decimals))
    vault.deposit(depositAmount, {"from": strategist})

    # Clone magic
    tx = strategy.clone(vault)
    cloned_strategy = Strategy.at(tx.return_value)
    assert cloned_strategy.numLenders() == 0

    tx = GenericCream.at(strategy.lenders(0)).cloneCreamLender(
        cloned_strategy, "Cream2", crHegic
    )
    cloned_lender = GenericCream.at(tx.return_value)
    assert cloned_lender.lenderName() == "Cream2"
    cloned_strategy.addLender(cloned_lender, {"from": gov})

    vault.addStrategy(cloned_strategy, 10_000, 0, 2 ** 256 - 1, 500, {"from": gov})
    assert cloned_strategy.harvestTrigger(1) == True
    cloned_strategy.harvest({"from": strategist})

    chain.mine(1)
    crHegic.mint(0, {"from": strategist})

    # whale deposits as well
    whale_deposit = 100_000 * (10 ** (decimals))
    vault.deposit(whale_deposit, {"from": whale})
    assert cloned_strategy.harvestTrigger(1000) == True
    cloned_strategy.harvest({"from": strategist})

    for i in range(15):
        waitBlock = random.randint(10, 50)
        crHegic.mint(0, {"from": whale})
        chain.sleep(15 * 30)
        chain.mine(waitBlock)

        cloned_strategy.harvest({"from": strategist})
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
    genericStateOfStrat(cloned_strategy, currency, vault)
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
    status = cloned_strategy.lendStatuses()

    chain.mine(waitBlock)
    withdrawn = balanceAfter - balanceBefore
    assert withdrawn > expectedout * 0.99 and withdrawn < expectedout * 1.01

    profit = balanceAfter - starting_balance
    assert profit > 0
    print(profit)


def test_double_initialize(
    gov, vault, strategy, hegic, GenericCream, crHegic,
):

    tx = GenericCream.at(strategy.lenders(0)).cloneCreamLender(
        strategy, "Cream2", crHegic
    )
    cloned_lender = GenericCream.at(tx.return_value)

    # Shouldn't be able to call super's initialize
    with brownie.reverts():
        cloned_lender.initialize(crHegic, {"from": gov})

    # Shouldn't be able to call GenericCream's initialize
    with brownie.reverts():
        cloned_lender.initialize(strategy, "Cream2", {"from": gov})

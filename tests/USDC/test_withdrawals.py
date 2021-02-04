from itertools import count
from brownie import Wei, reverts
from useful_methods import genericStateOfStrat, genericStateOfVault, deposit, sleep
import random
import brownie


# this test cycles through every plugin and checks we can add/remove lender and withdraw
def test_withdrawals_work(
    usdc,
    Strategy,
    crUsdc,
    cUsdc,
    interface,
    chain,
    whale,
    gov,
    strategist,
    rando,
    vault,
    strategy,
    fn_isolation,
):
    starting_balance = usdc.balanceOf(strategist)
    currency = usdc
    decimals = currency.decimals()

    usdc.approve(vault, 2 ** 256 - 1, {"from": whale})
    usdc.approve(vault, 2 ** 256 - 1, {"from": strategist})

    deposit_limit = 1_000_000_000 * (10 ** (decimals))
    debt_ratio = 10000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 500, {"from": gov})
    vault.setDepositLimit(deposit_limit, {"from": gov})
    
    status = strategy.lendStatuses()
    depositAmount = 501 * (10 ** (decimals))
    vault.deposit(depositAmount, {"from": strategist})

    # whale deposits as well
    whale_deposit = 100_000 * (10 ** (decimals))
    vault.deposit(whale_deposit, {"from": whale})

    strategy.harvest({"from": strategist})

    sleep(chain, 25)

    strategy.harvest({"from": strategist})

    for j in status:
        plugin = interface.IGeneric(j[3])
        strategy.safeRemoveLender(plugin)

        status2 = strategy.lendStatuses()

    assert currency.balanceOf(strategy) > (depositAmount + whale_deposit) * 0.999

    form = "{:.2%}"
    formS = "{:,.0f}"

    for j in status:
        plugin = interface.IGeneric(j[3])
        print("Testing ", j[0])
        strategy.addLender(j[3], {'from': gov})
        strategy.harvest({"from": strategist})

        assert plugin.nav() > (depositAmount + whale_deposit) * 0.999

        shareprice = vault.pricePerShare()

        shares = vault.balanceOf(strategist)
        expectedout = shares * (shareprice / 1e18) * (10 ** (decimals * 2))
        balanceBefore = currency.balanceOf(strategist)
        # print(f"Lender: {j[0]}, Deposits: {formS.format(plugin.nav()/1e6)}")

        vault.withdraw(vault.balanceOf(strategist), {"from": strategist})
        balanceAfter = currency.balanceOf(strategist)
        # print(f"after Lender: {j[0]}, Deposits: {formS.format(plugin.nav()/1e6)}")

        withdrawn = balanceAfter - balanceBefore
        assert withdrawn > expectedout * 0.99 and withdrawn < expectedout * 1.01

        shareprice = vault.pricePerShare()

        shares = vault.balanceOf(whale)
        expectedout = shares * (shareprice / 1e18) * (10 ** (decimals * 2))
        balanceBefore = currency.balanceOf(whale)
        vault.withdraw(vault.balanceOf(whale), {"from": whale})
        balanceAfter = currency.balanceOf(whale)

        withdrawn = balanceAfter - balanceBefore
        assert withdrawn > expectedout * 0.99 and withdrawn < expectedout * 1.01

        vault.deposit(whale_deposit, {"from": whale})
        vault.deposit(depositAmount, {"from": strategist})

        strategy.harvest({"from": strategist})
        strategy.safeRemoveLender(j[3])
        assert plugin.nav() < 1000000
        assert currency.balanceOf(strategy) > (depositAmount + whale_deposit) * 0.999

    # our humble strategist deposits some test funds

    # strategist withdraws
    shareprice = vault.pricePerShare()

    shares = vault.balanceOf(strategist)
    expectedout = shares * (shareprice / 1e18) * (10 ** (decimals * 2))
    balanceBefore = currency.balanceOf(strategist)

    # genericStateOfStrat(strategy, currency, vault)
    # genericStateOfVault(vault, currency)

    vault.withdraw(vault.balanceOf(strategist), {"from": strategist})
    balanceAfter = currency.balanceOf(strategist)

    # genericStateOfStrat(strategy, currency, vault)
    # genericStateOfVault(vault, currency)
    status = strategy.lendStatuses()

    chain.mine(1)
    withdrawn = balanceAfter - balanceBefore
    assert withdrawn > expectedout * 0.99 and withdrawn < expectedout * 1.01

    shareprice = vault.pricePerShare()

    shares = vault.balanceOf(whale)
    expectedout = shares * (shareprice / 1e18) * (10 ** (decimals * 2))
    balanceBefore = currency.balanceOf(whale)
    vault.withdraw(vault.balanceOf(whale), {"from": whale})
    balanceAfter = currency.balanceOf(whale)
    withdrawn = balanceAfter - balanceBefore
    assert withdrawn > expectedout * 0.99 and withdrawn < expectedout * 1.01

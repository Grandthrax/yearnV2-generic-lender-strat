from itertools import count
from brownie import Wei, reverts
from useful_methods import genericStateOfVault, genericStateOfStrat
import random
import brownie

def test_aave_clone(
    chain,
    usdc,
    whale,
    gov,
    strategist,
    rando,
    vault,
    Strategy,
    strategy,
    GenericAave,
    aUsdc,
):
    # Clone magic
    tx = strategy.clone(vault)
    cloned_strategy = Strategy.at(tx.return_value)
    cloned_strategy.setWithdrawalThreshold(
        strategy.withdrawalThreshold(), {"from": gov}
    )
    cloned_strategy.setDebtThreshold(strategy.debtThreshold(), {"from": gov})
    cloned_strategy.setProfitFactor(strategy.profitFactor(), {"from": gov})
    cloned_strategy.setMaxReportDelay(strategy.maxReportDelay(), {"from": gov})

    assert cloned_strategy.numLenders() == 0

    # Clone the aave lender
    original_aave = GenericAave.at(strategy.lenders(strategy.numLenders() - 1))
    tx = original_aave.cloneAaveLender(
        cloned_strategy, "ClonedAaveUSDC", aUsdc, False, {"from": gov}
    )
    cloned_lender = GenericAave.at(tx.return_value)
    assert cloned_lender.lenderName() == "ClonedAaveUSDC"

    cloned_strategy.addLender(cloned_lender, {"from": gov})
    
    with brownie.reverts():
        cloned_lender.initialize['address,bool'](aUsdc, False, {'from': gov})

    starting_balance = usdc.balanceOf(strategist)
    currency = usdc
    decimals = currency.decimals()

    usdc.approve(vault, 2 ** 256 - 1, {"from": whale})
    usdc.approve(vault, 2 ** 256 - 1, {"from": strategist})

    deposit_limit = 1_000_000_000 * (10 ** (decimals))
    debt_ratio = 10_000
    vault.addStrategy(cloned_strategy, debt_ratio, 0, 2 ** 256 - 1, 500, {"from": gov})
    vault.setDepositLimit(deposit_limit, {"from": gov})

    assert deposit_limit == vault.depositLimit()
    # our humble strategist deposits some test funds
    depositAmount = 501 * (10 ** (decimals))
    vault.deposit(depositAmount, {"from": strategist})

    assert cloned_strategy.estimatedTotalAssets() == 0
    chain.mine(1)
    assert cloned_strategy.harvestTrigger(1) == True

    cloned_strategy.harvest({"from": strategist})

    assert (
        cloned_strategy.estimatedTotalAssets() >= depositAmount * 0.999999
    )  # losing some dust is ok

    assert cloned_strategy.harvestTrigger(1) == False

    # whale deposits as well
    whale_deposit = 100_000 * (10 ** (decimals))
    vault.deposit(whale_deposit, {"from": whale})
    assert cloned_strategy.harvestTrigger(1000) == True

    cloned_strategy.harvest({"from": strategist})

    for i in range(15):
        waitBlock = random.randint(10, 50)
        chain.sleep(15 * 30)
        chain.mine(waitBlock)

        cloned_strategy.harvest({"from": strategist})
        chain.sleep(6 * 3600 + 1)  # to avoid sandwich protection
        chain.mine(1)

        action = random.randint(0, 9)
        if action < 3:
            percent = random.randint(50, 100)

            shareprice = vault.pricePerShare()

            shares = vault.balanceOf(whale)
            print("whale has:", shares)
            sharesout = int(shares * percent / 100)
            expectedout = sharesout * (shareprice / 1e18) * (10 ** (decimals * 2))

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
    shareprice = vault.pricePerShare()

    shares = vault.balanceOf(strategist)
    expectedout = shares * (shareprice / 1e18) * (10 ** (decimals * 2))
    balanceBefore = currency.balanceOf(strategist)

    status = cloned_strategy.lendStatuses()
    form = "{:.2%}"
    formS = "{:,.0f}"
    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e6)}, APR: {form.format(j[2]/1e18)}"
        )
    vault.withdraw(vault.balanceOf(strategist), {"from": strategist})
    balanceAfter = currency.balanceOf(strategist)
    status = cloned_strategy.lendStatuses()

    chain.mine(waitBlock)
    withdrawn = balanceAfter - balanceBefore
    assert withdrawn > expectedout * 0.99 and withdrawn < expectedout * 1.01

    profit = balanceAfter - starting_balance
    assert profit > 0
    print(profit)

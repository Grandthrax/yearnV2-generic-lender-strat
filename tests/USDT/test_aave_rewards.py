from itertools import count
from brownie import Wei, reverts, Contract, interface
from useful_methods import genericStateOfVault, genericStateOfStrat
import random
import brownie

def test_aave_rewards(chain,
    usdt,
    whale,
    gov,
    strategist,
    rando,
    vault,
    Strategy,
    strategy,
    GenericAave,
    aUsdt):
    # Clone magic
    tx = strategy.clone(vault, {'from': gov})
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
        cloned_strategy, "ClonedAaveUSDC", aUsdt, False, {"from": gov}
    )
    cloned_lender = GenericAave.at(tx.return_value)
    assert cloned_lender.lenderName() == "ClonedAaveUSDC"

    cloned_strategy.addLender(cloned_lender, {"from": gov})
    starting_balance = usdt.balanceOf(strategist)
    currency = usdt
    decimals = currency.decimals()

    usdt.approve(vault, 2 ** 256 - 1, {"from": whale})
    usdt.approve(vault, 2 ** 256 - 1, {"from": strategist})

    deposit_limit = 1_000_000_000 * (10 ** (decimals))
    debt_ratio = 10_000
    vault.addStrategy(cloned_strategy, debt_ratio, 0, 2 ** 256 - 1, 500, {"from": gov})
    vault.setDepositLimit(deposit_limit, {"from": gov})

    assert deposit_limit == vault.depositLimit()

    incentives_controller = Contract(aUsdt.getIncentivesController())
    assert incentives_controller.getDistributionEnd() > 0
    # ------------------ test starts ------------------
    # turning on claiming incentives logic
    cloned_lender.setIsIncentivised(True, {'from': gov})

    # our humble strategist deposits some test funds
    depositAmount = 50000 * (10 ** (decimals))
    vault.deposit(depositAmount, {"from": strategist})

    assert cloned_strategy.estimatedTotalAssets() == 0
    chain.mine(1)
    assert cloned_strategy.harvestTrigger(1) == True

    cloned_strategy.harvest({"from": gov})

    assert (
        cloned_strategy.estimatedTotalAssets() >= depositAmount * 0.999999
    )  # losing some dust is ok

    assert cloned_strategy.harvestTrigger(1) == False
    
    assert cloned_lender.harvestTrigger() == True # first harvest

    cloned_lender.harvest({'from': gov})

    assert cloned_lender.harvestTrigger() == False

    chain.sleep(10*3600*24+1) # we wait 10 days for the cooldown period 
    chain.mine(1)

    assert cloned_lender.harvestTrigger() == True
    assert incentives_controller.getRewardsBalance([aUsdt], cloned_lender) > 0
    previousBalance = aUsdt.balanceOf(cloned_lender)
    
    cloned_lender.harvest({'from': gov}) # redeem staked tokens, sell them, deposit them, claim rewards

    assert incentives_controller.getRewardsBalance([aUsdt], cloned_lender) == 0
    assert aUsdt.balanceOf(cloned_lender) > previousBalance # deposit sold rewards

    cloned_strategy.harvest({'from': gov})
    
    status = cloned_strategy.lendStatuses()
    form = "{:.2%}"
    formS = "{:,.0f}"
    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e6)}, APR: {form.format(j[2]/1e18)}"
        )
    chain.sleep(6*3600)
    chain.mine(1)
    vault.withdraw({"from": strategist})
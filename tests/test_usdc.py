from itertools import count
from brownie import Wei, reverts
from useful_methods import  genericStateOfVault,genericStateOfStrat
import random
import brownie

def test_good_migration(usdc,Strategy, chain, whale,gov,strategist,rando,vault, strategy):
    currency = usdc

    usdc.approve(vault, 2 ** 256 - 1, {"from": whale} )
    usdc.approve(vault, 2 ** 256 - 1, {"from": strategist} )

    
    deposit_limit = 1_000_000_000 *1e6
    vault.addStrategy(strategy, deposit_limit, deposit_limit, 500, {"from": strategist})
    
    amount1 = 500 *1e6
    vault.deposit(amount1, {"from": whale})

    amount1 = 50 *1e6
    vault.deposit(amount1, {"from": strategist})
    gov= strategist

    strategy.harvest({'from': gov})
    chain.sleep(30*13)
    chain.mine(30)

    strategy.harvest({'from': gov})

    strategy_debt = vault.strategies(strategy)[4]  # totalDebt
    prior_position = strategy.estimatedTotalAssets()
    assert strategy_debt > 0

    new_strategy = strategist.deploy(Strategy, vault)
    assert vault.strategies(new_strategy)[4] == 0
    assert currency.balanceOf(new_strategy) == 0

    # Only Governance can migrate
    with brownie.reverts():
        vault.migrateStrategy(strategy, new_strategy, {"from": rando})

    vault.migrateStrategy(strategy, new_strategy, {"from": gov})
    assert vault.strategies(strategy)[4] == 0
    assert vault.strategies(new_strategy)[4] == strategy_debt
    assert new_strategy.estimatedTotalAssets() > prior_position*0.999 or new_strategy.estimatedTotalAssets() < prior_position*1.001
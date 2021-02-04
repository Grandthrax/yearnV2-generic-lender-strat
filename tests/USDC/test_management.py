from itertools import count
from brownie import Wei, reverts
from useful_methods import genericStateOfVault, genericStateOfStrat
import random
import brownie

def test_manual_override(
    strategy, chain, vault, currency, interface, whale, strategist, gov, rando
):

    decimals = currency.decimals()

    deposit_limit = 100_000_000 * (10 ** decimals)
    vault.addStrategy(strategy, 9800, 0, 2 ** 256 - 1, 500, {"from": gov})

    amount1 = 50 * (10 ** decimals)
    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    currency.approve(vault, 2 ** 256 - 1, {"from": strategist})

    vault.setDepositLimit(deposit_limit, {'from': gov})
    assert vault.depositLimit() > 0

    amount2 = 50_000 * (10 ** decimals)

    vault.deposit(amount1, {"from": strategist})
    vault.deposit(amount2, {"from": whale})

    strategy.harvest({"from": strategist})

    status = strategy.lendStatuses()

    for j in status:
        plugin = interface.IGeneric(j[3])

        with brownie.reverts("!management"):
            plugin.emergencyWithdraw(1, {"from": rando})
        with brownie.reverts("!management"):
            plugin.withdrawAll({"from": rando})
        with brownie.reverts("!management"):
            plugin.deposit({"from": rando})
        with brownie.reverts("!management"):
            plugin.withdraw(1, {"from": rando})

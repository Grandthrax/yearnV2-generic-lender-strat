from itertools import count
from brownie import Wei, reverts, Contract, chain
from useful_methods import genericStateOfVault, genericStateOfStrat
import random


def test_basic(vault, strategy, snx, snx_whale, cySNX):

    gov = vault.governance()
    snx.approve(vault, 2 ** 256 - 1, {"from": snx_whale})
    vault.deposit(Wei("1_000 ether"), {"from": snx_whale})

    s0 = Contract(vault.withdrawalQueue(0))
    debt_ratio = vault.strategies(s0).dict()["debtRatio"]
    assert debt_ratio > 0
    vault.updateStrategyDebtRatio(s0, 0, {"from": gov})

    # Invest only 1k SNX
    vault.addStrategy(strategy, debt_ratio, 0, Wei("1_000 ether"), 1000, {"from": gov})
    strategy.harvest({"from": gov})

    # No more deposits into the strategy
    vault.updateStrategyMaxDebtPerHarvest(strategy, 0, {"from": gov})

    chain.mine(2000)
    chain.sleep(3600 * 8)
    cySNX.mint(0, {"from": gov})
    strategy.harvest({"from": gov})

    assert vault.strategies(strategy).dict()["totalGain"] > 0
    assert vault.strategies(strategy).dict()["totalLoss"] == 0

    strategy.setEmergencyExit({"from": gov})
    strategy.harvest({"from": gov})

    assert vault.strategies(strategy).dict()["totalLoss"] == 0
    assert vault.strategies(strategy).dict()["totalDebt"] <= 1

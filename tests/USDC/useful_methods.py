import brownie
import requests
from brownie.network.state import Chain


def genericStateOfStrat(strategy, currency, vault):
    decimals = currency.decimals()
    print(f"\n----state of {strategy.name()}----")

    print("Want:", currency.balanceOf(strategy) / (1 ** decimals))
    print("Total assets estimate:", strategy.estimatedTotalAssets() / (10 ** decimals))
    strState = vault.strategies(strategy)
    totalDebt = strState[5] / (10 ** decimals)
    debtLimit = strState[2] / (10 ** decimals)

    totalReturns = strState[6] / (10 ** decimals)
    print(f"Total Strategy Debt: {totalDebt:.5f}")
    print(f"Strategy Debt Limit: {debtLimit:.5f}")
    print(f"Total Strategy Returns: {totalReturns:.5f}")
    print("Harvest Trigger:", strategy.harvestTrigger(1000000 * 30 * 1e9))
    print(
        "Tend Trigger:", strategy.tendTrigger(1000000 * 30 * 1e9)
    )  # 1m gas at 30 gwei
    print("Emergency Exit:", strategy.emergencyExit())


def genericStateOfVault(vault, currency):
    decimals = currency.decimals()
    print(f"\n----state of {vault.name()} vault----")
    balance = vault.totalAssets() / (10 ** decimals)
    print(f"Total Assets: {balance:.5f}")
    balance = vault.totalDebt() / (10 ** decimals)
    print("Loose balance in vault:", currency.balanceOf(vault) / (10 ** decimals))
    print(f"Total Debt: {balance:.5f}")


def deposit(amount, user, dai, vault):
    # print('\n----user deposits----')
    dai.approve(vault, amount, {"from": user})
    # print('deposit amount:', amount.to('ether'))
    vault.deposit(amount, {"from": user})


def sleep(chain, blocks):
    timeN = chain.time()
    endTime = blocks * 13 + timeN
    chain.mine(blocks, endTime)

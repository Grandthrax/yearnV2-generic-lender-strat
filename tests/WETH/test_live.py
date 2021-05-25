from itertools import count
from brownie import Wei, reverts
from useful_methods import genericStateOfStrat, genericStateOfVault, deposit, sleep
import random
import brownie


def xtest_030_live(
    currency,
    interface,
    samdev,
    Contract,
    devychad,
    live_guest_list,
    AlphaHomo,
    live_vault_weth_031,
    live_strat_weth_031,
    chain,
    whale,
    gov,
    weth,
    rando,
    fn_isolation,
):
    gov = samdev
    decimals = currency.decimals()
    strategist = samdev

    vault = live_vault_weth_031
    strategy = live_strat_weth_031

    weth.approve(vault, 2 ** 256 - 1, {"from": whale})
    firstDeposit = 100 * 1e18

    vault.deposit(firstDeposit, {"from": whale})

    strategy.harvest({"from": strategist})

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    form = "{:.2%}"
    formS = "{:,.0f}"

    status = strategy.lendStatuses()

    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
        )


def xtest_live(
    currency,
    interface,
    samdev,
    Contract,
    devychad,
    live_guest_list,
    live_Alpha_Homo,
    live_vault_weth,
    live_strat_weth_1,
    chain,
    whale,
    gov,
    rando,
    fn_isolation,
):
    gov = devychad
    decimals = currency.decimals()
    strategist = samdev
    strategy = live_strat_weth_1
    vault = live_vault_weth

    addresses = [whale]
    permissions = [True]
    live_guest_list.setGuests(addresses, permissions, {"from": gov})
    strategy.addLender(live_dydxweth, {"from": strategist})

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    currency.approve(vault, 2 ** 256 - 1, {"from": strategist})

    whale_deposit = 100 * (10 ** (decimals))
    vault.deposit(whale_deposit, {"from": whale})

    strategy.harvest({"from": strategist})

    form = "{:.2%}"
    formS = "{:,.0f}"

    status = strategy.lendStatuses()

    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
        )


def test_live2(
    currency,
    interface,
    samdev,
    Contract,
    ychad,
    live_Alpha_Homo_2,
    live_vault_weth_2,
    live_strat_weth_2,
    chain,
    whale,
    gov,
    rando,
    fn_isolation,
    accounts
):
    gov = ychad
    decimals = currency.decimals()
    strategist = samdev
    strategy = live_strat_weth_2
    vault = live_vault_weth_2
    ms = accounts.at("0x16388463d60ffe0661cf7f1f31a7d658ac790ff7", force=True)
    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)

    vault.updateStrategyDebtRatio(strategy, 0, {"from": ms})
    strategy.harvest({"from": ms})
    

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    #currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    #currency.approve(vault, 2 ** 256 - 1, {"from": rando})

    #whale_deposit = 100 * (10 ** (decimals))
    #currency.transfer(rando, whale_deposit, {"from": whale})
    #vault.deposit(whale_deposit, {"from": whale})

    
    

    form = "{:.2%}"
    formS = "{:,.0f}"

    status = strategy.lendStatuses()

    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
        )

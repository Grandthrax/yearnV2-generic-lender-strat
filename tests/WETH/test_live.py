from itertools import count
from brownie import Wei, reverts
from useful_methods import genericStateOfStrat, genericStateOfVault, deposit, sleep
import random
import brownie


def test_live(currency,interface,samdev,devychad,live_guest_list,live_Alpha_Homo,live_vault_weth,live_strat_weth_1, chain, whale,gov,rando, fn_isolation):
    gov =devychad
    decimals = currency.decimals()
    strategist = samdev
    strategy = live_strat_weth_1
    vault = live_vault_weth

    addresses = [whale]
    permissions = [True]
    live_guest_list.setGuests(addresses, permissions, {"from": gov})
    # strategy.addLender(live_dydxweth, {"from": strategist})

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    currency.approve(vault, 2 ** 256 - 1, {"from": whale} )
    currency.approve(vault, 2 ** 256 - 1, {"from": strategist} )

    whale_deposit  =100 *(10 ** (decimals))
    vault.deposit(whale_deposit, {"from": whale})

    strategy.harvest({"from": strategist})

    form = "{:.2%}"
    formS = "{:,.0f}"

    status = strategy.lendStatuses()

    for j in status:
        print(f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}")
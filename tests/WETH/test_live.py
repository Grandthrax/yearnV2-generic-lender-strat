from itertools import count
from brownie import Wei, reverts
from useful_methods import genericStateOfStrat, genericStateOfVault, deposit, sleep
import random
import brownie


def test_live(currency,interface,samdev,Contract, devychad,live_guest_list,live_Alpha_Homo,live_vault_weth,live_strat_weth_1, chain, whale,gov,rando, fn_isolation):
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

def test_live2(currency,interface,samdev,Contract,ychad,live_Alpha_Homo_2,live_vault_weth_2,live_strat_weth_2, chain, whale,gov,rando, fn_isolation):
    gov =ychad
    decimals = currency.decimals()
    strategist = samdev
    strategy = live_strat_weth_2
    vault = live_vault_weth_2

    addresses = [whale]
    permissions = [True]
    # strategy.addLender(live_dydxweth, {"from": strategist})
    print(strategy)
    print(vault)
    guestList= Contract('0xcB16133a37Ef19F90C570B426292BDcca185BF47')
    vault.setDepositLimit(500*1e18, {'from': gov})
    vault.setGuestList(guestList, {'from': gov})
    print("guest list, ", vault.guestList() )
    vault.addStrategy(strategy, 500*1e18, 500*1e18, 1000, {"from": gov})

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    currency.approve(vault, 2 ** 256 - 1, {"from": whale} )
    currency.approve(vault, 2 ** 256 - 1, {"from": rando} )

    whale_deposit  =100 *(10 ** (decimals))
    currency.transfer(rando, whale_deposit, {'from': whale})
    vault.deposit(whale_deposit, {"from": whale})

    strategy.harvest({"from": strategist})

    form = "{:.2%}"
    formS = "{:,.0f}"

    status = strategy.lendStatuses()

    for j in status:
        print(f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}")
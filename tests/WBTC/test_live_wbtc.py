from itertools import count
from brownie import Wei, reverts
from useful_methods import genericStateOfStrat, genericStateOfVault, deposit, sleep
import random


def test_cream_up_down(
    interface,
    samdev,
    Contract,
    devychad,
    live_vault_wbtc,
    GenericCream,
    crWbtc,
    chain,
    accounts,
    Strategy,
    gov,
    rando,
    fn_isolation
):
    vault = live_vault_wbtc
    currency = interface.ERC20(vault.token())
    decimals = currency.decimals()
    strategist = samdev
    gov = accounts.at(vault.governance(), force=True)
    strategy = Strategy.at('0xe9bD008A97e362F7C501F6F5532A348d2e6B8131')

    reduce_strat = Contract(vault.withdrawalQueue(0))
    vault.updateStrategyDebtRatio(reduce_strat, 7000,{"from": gov})
    vault.updateStrategyDebtRatio(strategy, 25,{"from": gov})
    reduce_strat.harvest({"from": gov})

    #creamPlugin = strategist.deploy(GenericCream, strategy, "Ironbank", crWbtc)
    creamPlugin = GenericCream.at('0x5D3386b5f893774bd2d6c5A1EdE2a88F46639FA3')
    strategy.addLender(creamPlugin, {"from": gov})

    
    form = "{:.2%}"
    formS = "{:,.0f}"
    chain.mine(5)
    crWbtc.mint(0, {"from": strategist})
    chain.mine(5)

    strategy.harvest({"from": gov})
    chain.mine(5)
    crWbtc.mint(0, {"from": strategist})
    chain.mine(5)

    status = strategy.lendStatuses()
    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/(10**decimals))} APR: {form.format(j[2]/1e18)}"
        )

    print("\n safe remove lender")
    chain.mine(5)
    crWbtc.mint(0, {"from": strategist})
    chain.mine(5)
    strategy.safeRemoveLender(creamPlugin, {"from": gov})
    chain.mine(5)
    crWbtc.mint(0, {"from": strategist})
    chain.mine(5)
    
    strategy.harvest({"from": gov})
    status = strategy.lendStatuses()
    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/(10**decimals))} APR: {form.format(j[2]/1e18)}"
        )
    
    print("\n readd lender")
    strategy.addLender(creamPlugin, {"from": gov})
    chain.mine(5)
    crWbtc.mint(0, {"from": strategist})
    chain.mine(5)
    strategy.harvest({"from": gov})
    status = strategy.lendStatuses()
    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/(10**decimals))} APR: {form.format(j[2]/1e18)}"
        )

    print("\n 0 debt ratio")
    vault.updateStrategyDebtRatio(strategy, 0,{"from": gov})
    chain.mine(5)
    crWbtc.mint(0, {"from": strategist})
    chain.mine(5)

    strategy.harvest({"from": gov})
    status = strategy.lendStatuses()
    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/(10**decimals))} APR: {form.format(j[2]/1e18)}"
        )
    genericStateOfStrat(strategy, currency, vault)
    



    

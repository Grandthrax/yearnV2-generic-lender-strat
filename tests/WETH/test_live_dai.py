from itertools import count
from brownie import Wei, reverts
from useful_methods import genericStateOfStrat, genericStateOfVault, deposit, sleep
import random
import brownie

def test_030_live_dai(
    dai,
    interface,
    samdev,
    Contract,
    devychad,
    crDai,
    Strategy,
    daddy,
    live_guest_list,
    GenericDyDx,
    GenericCream,
    live_vault_dai_030,
    live_strat_weth_032,
    live_strat_dai_030,
    live_dydxdai,
    live_creamdai,
    chain,
    whale,
    gov,
    weth,
    accounts,
    rando,
    fn_isolation,
):
    gov = daddy
    currency = dai
    decimals = currency.decimals()
    strategist = samdev
    #dydxPlugin = strategist.deploy(GenericDyDx, strategy, "DyDx")
    #creamPlugin = strategist.deploy(GenericCream, strategy, "Cream", crDai)
    dydxPlugin = live_dydxdai
    creamPlugin = live_creamdai


    vault = live_vault_dai_030
    #tx = live_strat_weth_032.clone(vault, {'from': strategist})
    #strategy = Strategy.at(tx.events['Cloned']["clone"])
    strategy = live_strat_dai_030

    form = "{:.2%}"
    formS = "{:,.0f}"

    manualAll = [[dydxPlugin, 0], [creamPlugin, 1000]]
    strategy.manualAllocation(manualAll, {"from": strategist})
    #print("new alloc")

    status = strategy.lendStatuses()

    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
        )

    #strategy.setDebtThreshold(1_000_000 *1e18, {'from': strategist})
    #strategy.setProfitFactor(1000, {'from': strategist})

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)


    vault = Contract('0x19D3364A399d251E894aC732651be8B0E4e85001')
    strategy = Contract('0x32b8C26d0439e1959CEa6262CBabC12320b384c4')

    dydxP = '0xed2F20ACbb4809BB2F62da75cbE3A0Df557d955E'
    creamP = '0xC53a7A7bEB51141b750b2752cD1276150a511daa'

    #vault.setDepositLimit(300_000_000 *1e18, {"from": gov})
    #vault.addStrategy(strategy, 100, 0, 1000, {"from": gov})
    #strategy.addLender(creamP, {"from": gov})
    #strategy.addLender(dydxP, {"from": gov})

    #strategy.harvest({"from": strategist})
    #lev_comp = "0x4031afd3B0F71Bace9181E554A9E680Ee4AbE7dF"
    #alpha2 = "0x7D960F3313f3cB1BBB6BF67419d303597F3E2Fa8"
    #ib_lev_comp = "0x77b7CD137Dd9d94e7056f78308D7F65D2Ce68910"
    #gen_lender = "0x32b8C26d0439e1959CEa6262CBabC12320b384c4"
    #vault.updateStrategyDebtRatio(lev_comp, 6_000, {"from": gov})
    #vault.updateStrategyDebtRatio(alpha2, 2_000, {"from": gov})
    #vault.updateStrategyDebtRatio(ib_lev_comp, 100, {"from": gov})
    #vault.updateStrategyDebtRatio(gen_lender, 1_800, {"from": gov})


    #assert vault.debtRatio() == 9_900
    
    #strategy.harvest({"from": strategist})

    #manualAll = [[dydxPlugin, 700], [creamPlugin, 300]]
    #strategy.manualAllocation(manualAll, {"from": strategist})
    #print("new alloc")

    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)

    #form = "{:.2%}"
    #formS = "{:,.0f}"

    #status = strategy.lendStatuses()

    #for j in status:
    #    print(
    #        f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
    #    )
    #chain.sleep(100)
    #chain.mine(1)
    

    #vault.updateStrategyDebtRatio(strategy, 0, {'from': gov})
    #strategy.harvest({"from": strategist})
    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)
    #status = strategy.lendStatuses()

    #for j in status:
    #    print(
    #        f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
    #    )


def test_revoke_all(
    dai,
    interface,
    samdev,
    Contract,
    devychad,
    crDai,
    Strategy,
    daddy,
    live_guest_list,
    GenericDyDx,
    GenericCream,
    live_vault_dai_030,
    live_strat_weth_032,
    live_strat_dai_030,
    live_dydxdai,
    live_creamdai,
    chain,
    whale,
    gov,
    weth,
    accounts,
    rando,
    fn_isolation,
):

    whale = accounts.at('0x014de182c147f8663589d77eadb109bf86958f13', force=True)
    gov = daddy
    currency = dai
    decimals = currency.decimals()
    strategist = samdev
    #dydxPlugin = strategist.deploy(GenericDyDx, strategy, "DyDx")
    #creamPlugin = strategist.deploy(GenericCream, strategy, "Cream", crDai)
    dydxPlugin = live_dydxdai
    creamPlugin = live_creamdai


    vault = live_vault_dai_030
    #tx = live_strat_weth_032.clone(vault, {'from': strategist})
    #strategy = Strategy.at(tx.events['Cloned']["clone"])
    strategy = Strategy.at(vault.withdrawalQueue(0))

    vault.revokeStrategy(strategy, {'from': gov})
    vault.removeStrategyFromQueue(s1, {'from': gov})
    #vault.updateStrategyDebtRatio(strategy, 0, {'from': gov})
    strategy.harvest({"from": strategist})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

from itertools import count
from brownie import Wei, reverts
from useful_methods import genericStateOfVault, genericStateOfStrat
import random
import brownie

def test_normal_activity(
    usdt,
    Strategy,
    crUsdt,
    samdev,
    cUsdt,
    chain,
    whale,
    daddy,
    currency,
    strategist,
    rando,
    vault,
    strategy,
    Contract,
    accounts,
    fn_isolation,
    aUsdt,
):
    strategist = accounts.at(strategy.strategist(), force=True)
    gov = accounts.at(vault.governance(), force=True)
    starting_balance = currency.balanceOf(strategist)

    decimals = currency.decimals()
    #print(vault.withdrawalQueue(1))

    #strat2 = Contract(vault.withdrawalQueue(1))

    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    currency.approve(vault, 2 ** 256 - 1, {"from": strategist})

    deposit_limit = 1_000_000_000 * (10 ** (decimals))
    debt_ratio = 10_000
    
    #vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 500, {"from": gov})
    vault.setDepositLimit(deposit_limit, {"from": gov})

    assert deposit_limit == vault.depositLimit()
    # our humble strategist deposits some test funds
    depositAmount = 501 * (10 ** (decimals))
    vault.deposit(depositAmount, {"from": strategist})

    assert strategy.estimatedTotalAssets() == 0
    chain.mine(1)
    assert strategy.harvestTrigger(1) == True

    strategy.harvest({"from": strategist})

    #assert (
    #    strategy.estimatedTotalAssets() >= depositAmount * 0.999999
    #)  # losing some dust is ok

    assert strategy.harvestTrigger(1) == False
    # whale deposits as well
    whale_deposit = 1_000_000 * (10 ** (decimals))
    vault.deposit(whale_deposit, {"from": whale})
    assert strategy.harvestTrigger(1000) == True

    strategy.harvest({"from": strategist})
    #strat2.harvest({"from": gov})
    status = strategy.lendStatuses()
    form = "{:.2%}"
    formS = "{:,.0f}"
    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e6)} APR: {form.format(j[2]/1e18)}"
        )

    for i in range(5):
        waitBlock = random.randint(10, 50)
        cUsdt.mint(0, {"from": whale})
        crUsdt.mint(0, {"from": whale})
        chain.sleep(15 * 30)
        chain.mine(waitBlock)

        strategy.harvest({"from": strategist})
        #strat2.harvest({"from": gov})
        chain.sleep(6 * 3600 + 1)  # to avoid sandwich protection
        chain.mine(1)

        action = random.randint(0, 9)
        if action < 3:
            percent = random.randint(50, 100)

            shareprice = vault.pricePerShare()

            shares = vault.balanceOf(whale)
            print("whale has:", shares)
            sharesout = int(shares * percent / 100)
            expectedout = sharesout * (shareprice / 1e18) * (10 ** (decimals * 2))

            balanceBefore = currency.balanceOf(whale)
            vault.withdraw(sharesout, {"from": whale})
            chain.mine(waitBlock)
            balanceAfter = currency.balanceOf(whale)

            withdrawn = balanceAfter - balanceBefore
            assert withdrawn > expectedout * 0.99 and withdrawn < expectedout * 1.01

        elif action < 5:
            print("whale deposits:")
            depositAm = random.randint(10, 100) * (10 ** decimals)
            vault.deposit(depositAm, {"from": whale})

        status = strategy.lendStatuses()
        form = "{:.2%}"
        formS = "{:,.0f}"
        for j in status:
            print(
                f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e6)}, APR: {form.format(j[2]/1e18)}"
            )

    # strategist withdraws
    shareprice = vault.pricePerShare()

    shares = vault.balanceOf(strategist)
    expectedout = shares * (shareprice / 1e18) * (10 ** (decimals * 2))
    balanceBefore = currency.balanceOf(strategist)

    # genericStateOfStrat(strategy, currency, vault)
    # genericStateOfVault(vault, currency)
    vault.transferFrom(strategy, strategist, vault.balanceOf(strategy), {"from": strategist})
    vault.withdraw(vault.balanceOf(strategist), {"from": strategist})

    vault.withdraw(vault.balanceOf(whale), {"from": whale})
    status = strategy.lendStatuses()
    form = "{:.2%}"
    formS = "{:,.0f}"
    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e6)}, APR: {form.format(j[2]/1e18)}"
        )
    
    balanceAfter = currency.balanceOf(strategist)

    # genericStateOfStrat(strategy, currency, vault)
    # genericStateOfVault(vault, currency)
    status = strategy.lendStatuses()

    chain.mine(waitBlock)
    withdrawn = balanceAfter - balanceBefore
    assert withdrawn > expectedout * 0.99 and withdrawn < expectedout * 1.01

    profit = balanceAfter - starting_balance
    assert profit > 0
    print(profit)


def test_cream_up_down(
    usdt,
    Strategy,
    crUsdt,
    samdev,
    GenericCream,
    cUsdt,
    live_strat_weth_1,
    chain,
    whale,
    daddy,
    currency,
    strategist,
    rando,
    vault,
    Contract,
    accounts,
    fn_isolation,
    aUsdt,
):

    gov = accounts.at(vault.governance(), force=True)
    tx = live_strat_weth_1.clone(vault, {"from": strategist})
    strategy = Strategy.at(tx.return_value)
    
    strategy.setRewards(strategist, {"from": strategist})
    strategy.setWithdrawalThreshold(0, {"from": strategist})

    creamPlugin = strategist.deploy(GenericCream, strategy, "Cream", crUsdt)

    strategy.addLender(creamPlugin, {"from": gov})

    strategy.setDebtThreshold(1*1e6, {"from": gov})
    strategy.setProfitFactor(1500, {"from": gov})
    strategy.setMaxReportDelay(86000, {"from": gov})

    starting_balance = currency.balanceOf(strategist)

    decimals = currency.decimals()
    #print(vault.withdrawalQueue(1))

    #strat2 = Contract(vault.withdrawalQueue(1))

    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    currency.approve(vault, 2 ** 256 - 1, {"from": strategist})

    deposit_limit = 1_000_000_000 * (10 ** (decimals))
    debt_ratio = 10_000
    
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 500, {"from": gov})
    vault.setDepositLimit(deposit_limit, {"from": gov})

    assert deposit_limit == vault.depositLimit()
    # our humble strategist deposits some test funds
    depositAmount = 501 * (10 ** (decimals))
    vault.deposit(depositAmount, {"from": strategist})

    assert strategy.estimatedTotalAssets() == 0
    chain.mine(1)

    strategy.harvest({"from": strategist})

    #assert (
    #    strategy.estimatedTotalAssets() >= depositAmount * 0.999999
    #)  # losing some dust is ok
    # whale deposits as well
    whale_deposit = 1_000_000 * (10 ** (decimals))
    vault.deposit(whale_deposit, {"from": whale})
    assert strategy.harvestTrigger(1000) == True

    strategy.harvest({"from": strategist})
    #strat2.harvest({"from": gov})
    status = strategy.lendStatuses()
    form = "{:.2%}"
    formS = "{:,.0f}"
    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e6)}, APR: {form.format(j[2]/1e18)}"
        )
    chain.mine(20)
    crUsdt.mint(0, {"from": strategist})


    vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    strategy.harvest({"from": strategist})
    print(crUsdt.balanceOf(creamPlugin))
    print(creamPlugin.hasAssets())
    chain.mine(20)
    crUsdt.mint(0, {"from": strategist})
    chain.mine(10)
    strategy.harvest({"from": strategist})
    
    print(crUsdt.balanceOf(creamPlugin))
    print(creamPlugin.hasAssets())
    chain.mine(20)
    crUsdt.mint(0, {"from": strategist})

    chain.mine(10)
    strategy.harvest({"from": strategist})
    print(creamPlugin.hasAssets())
    print(crUsdt.balanceOf(creamPlugin))
    status = strategy.lendStatuses()
    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e6)}, APR: {form.format(j[2]/1e18)}"
        )
    chain.mine(20)
    crUsdt.mint(0, {"from": strategist})
    vault.updateStrategyDebtRatio(strategy, 10_000, {"from": gov})
    strategy.harvest({"from": strategist})

    strategy.harvest({"from": strategist})
    status = strategy.lendStatuses()
    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e6)}, APR: {form.format(j[2]/1e18)}"
        )



def test_apr_live_usdt(
    dai,
    interface,
    samdev,
    Contract,
    crUsdt,
    cUsdt,
    aUsdt,
    daddy,
    vault,
    currency,
    GenericDyDx,
    GenericCream,
    strategy,
    chain,
    whale,
    gov,
    weth,
    accounts,
    rando,
    fn_isolation
):
    gov = accounts.at(vault.governance(), force=True)
    decimals = currency.decimals()
    strategist = samdev
    

    form = "{:.2%}"
    formS = "{:,.0f}"

    #manualAll = [[dydxPlugin, 0], [creamPlugin, 1000]]
    #strategy.manualAllocation(manualAll, {"from": strategist})
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

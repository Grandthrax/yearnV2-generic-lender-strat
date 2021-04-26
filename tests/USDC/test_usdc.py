from itertools import count
from brownie import Wei, reverts
from useful_methods import genericStateOfVault, genericStateOfStrat
import random
import brownie


def test_good_migration(
    usdc, Strategy, chain, whale, gov, strategist, rando, vault, strategy, fn_isolation
):
    currency = usdc

    usdc.approve(vault, 2 ** 256 - 1, {"from": whale})
    usdc.approve(vault, 2 ** 256 - 1, {"from": strategist})

    deposit_limit = 1_000_000_000 * 1e6
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 500, {"from": gov})
    vault.setDepositLimit(deposit_limit, {"from": gov})

    amount1 = 500 * 1e6
    vault.deposit(amount1, {"from": whale})

    amount1 = 50 * 1e6
    vault.deposit(amount1, {"from": strategist})

    strategy.harvest({"from": strategist})
    chain.sleep(30 * 13)
    chain.mine(30)

    strategy.harvest({"from": strategist})

    strategy_debt = vault.strategies(strategy)[6]  # totalDebt
    print(vault.strategies(strategy).dict())
    prior_position = strategy.estimatedTotalAssets()
    assert strategy_debt > 0

    new_strategy = strategist.deploy(Strategy, vault)
    assert vault.strategies(new_strategy)[6] == 0
    assert currency.balanceOf(new_strategy) == 0

    # Only Governance can migrate
    with brownie.reverts():
        vault.migrateStrategy(strategy, new_strategy, {"from": rando})

    tx = vault.migrateStrategy(strategy, new_strategy, {"from": gov})
    print(tx.events)
    assert vault.strategies(strategy)[6] == 0
    assert vault.strategies(new_strategy)[6] == strategy_debt
    assert (
        new_strategy.estimatedTotalAssets() > prior_position * 0.999
        or new_strategy.estimatedTotalAssets() < prior_position * 1.001
    )


def test_normal_activity(
    usdc,
    Strategy,
    crUsdc,
    cUsdc,
    chain,
    whale,
    gov,
    strategist,
    rando,
    vault,
    strategy,
    fn_isolation,
    aUsdc,
):
    starting_balance = usdc.balanceOf(strategist)
    currency = usdc
    decimals = currency.decimals()

    usdc.approve(vault, 2 ** 256 - 1, {"from": whale})
    usdc.approve(vault, 2 ** 256 - 1, {"from": strategist})

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
    assert strategy.harvestTrigger(1) == True

    strategy.harvest({"from": strategist})

    assert (
        strategy.estimatedTotalAssets() >= depositAmount * 0.999999
    )  # losing some dust is ok

    assert strategy.harvestTrigger(1) == False

    # whale deposits as well
    whale_deposit = 100_000 * (10 ** (decimals))
    vault.deposit(whale_deposit, {"from": whale})
    assert strategy.harvestTrigger(1000) == True

    strategy.harvest({"from": strategist})

    for i in range(15):
        waitBlock = random.randint(10, 50)
        cUsdc.mint(0, {"from": whale})
        crUsdc.mint(0, {"from": whale})
        chain.sleep(15 * 30)
        chain.mine(waitBlock)

        strategy.harvest({"from": strategist})
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
            depositAm = random.randint(10, 100) * (10 ** decimals)
            vault.deposit(depositAm, {"from": whale})

    # strategist withdraws
    shareprice = vault.pricePerShare()

    shares = vault.balanceOf(strategist)
    expectedout = shares * (shareprice / 1e18) * (10 ** (decimals * 2))
    balanceBefore = currency.balanceOf(strategist)

    # genericStateOfStrat(strategy, currency, vault)
    # genericStateOfVault(vault, currency)
    status = strategy.lendStatuses()
    form = "{:.2%}"
    formS = "{:,.0f}"
    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e6)}, APR: {form.format(j[2]/1e18)}"
        )
    vault.withdraw(vault.balanceOf(strategist), {"from": strategist})
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


def test_debt_increase(
    usdc, Strategy, chain, whale, gov, strategist, rando, vault, strategy, fn_isolation
):

    currency = usdc
    usdc.approve(vault, 2 ** 256 - 1, {"from": whale})

    deposit_limit = 100_000_000 * 1e6
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 500, {"from": gov})
    vault.setDepositLimit(deposit_limit, {"from": gov})
    form = "{:.2%}"
    formS = "{:,.0f}"
    firstDeposit = 2000_000 * 1e6
    predictedApr = strategy.estimatedFutureAPR(firstDeposit)
    print(
        f"Predicted APR from {formS.format(firstDeposit/1e6)} deposit: {form.format(predictedApr/1e18)}"
    )
    vault.deposit(firstDeposit, {"from": whale})
    print("Deposit: ", formS.format(firstDeposit / 1e6))
    strategy.harvest({"from": strategist})
    realApr = strategy.estimatedAPR()
    print("Current APR: ", form.format(realApr / 1e18))
    status = strategy.lendStatuses()

    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e6)}, APR: {form.format(j[2]/1e18)}"
        )

    assert realApr > predictedApr * 0.999 and realApr < predictedApr * 1.001

    predictedApr = strategy.estimatedFutureAPR(firstDeposit * 2)
    print(
        f"\nPredicted APR from {formS.format(firstDeposit/1e6)} deposit: {form.format(predictedApr/1e18)}"
    )
    print("Deposit: ", formS.format(firstDeposit / 1e6))
    vault.deposit(firstDeposit, {"from": whale})

    strategy.harvest({"from": strategist})
    realApr = strategy.estimatedAPR()

    print(f"Real APR after deposit: {form.format(realApr/1e18)}")
    status = strategy.lendStatuses()

    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e6)}, APR: {form.format(j[2]/1e18)}"
        )
    assert realApr > predictedApr * 0.999 and realApr < predictedApr * 1.001


def test_vault_shares(
    strategy,
    chain,
    vault,
    cUsdc,
    crUsdc,
    rewards,
    currency,
    gov,
    interface,
    whale,
    strategist,
    fn_isolation,
):
    deposit_limit = 100_000_000 * 1e6
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 500, {"from": gov})
    vault.setDepositLimit(deposit_limit, {"from": gov})
    decimals = currency.decimals()
    amount1 = 100_000 * (10 ** decimals)

    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    currency.approve(vault, 2 ** 256 - 1, {"from": strategist})

    vault.deposit(amount1, {"from": whale})
    vault.deposit(amount1, {"from": strategist})

    whale_share = vault.balanceOf(whale)
    gov_share = vault.balanceOf(strategist)

    assert gov_share == whale_share
    assert vault.pricePerShare() == (10 ** decimals)
    assert vault.pricePerShare() * whale_share / (10 ** decimals) == amount1

    assert (
        vault.pricePerShare() * whale_share / (10 ** decimals)
        == vault.totalAssets() / 2
    )
    assert gov_share == whale_share  # duplicated?

    strategy.harvest({"from": strategist})

    # no profit yet
    whale_share = vault.balanceOf(whale)
    gov_share = vault.balanceOf(strategist)
    rew_share = vault.balanceOf(
        strategy
    )  # rewards accumulated in Strategy until claimed by "rewards"

    assert (
        gov_share == whale_share and rew_share == 0 and whale_share == amount1
    )  # no profit yet, same shares distribution than initially
    assert (
        vault.pricePerShare() * (whale_share + rew_share + gov_share) / (10 ** decimals)
        > vault.totalAssets() * 0.999
        and vault.pricePerShare()
        * (whale_share + rew_share + gov_share)
        / (10 ** decimals)
        < vault.totalAssets() * 1.001
    )

    chain.sleep(13 * 1000)
    chain.mine(1000)

    whale_share = vault.balanceOf(whale)
    gov_share = vault.balanceOf(strategist)
    rew_share = vault.balanceOf(rewards)
    # no profit just aum fee. meaning total balance should be the same
    assert (
        (gov_share + whale_share + rew_share) * vault.pricePerShare() / (10 ** decimals)
        > amount1 * 2 * 0.999
        and (gov_share + whale_share + rew_share)
        * vault.pricePerShare()
        / (10 ** decimals)
        < amount1 * 2 * 1.001
    )
    cUsdc.mint(0, {"from": whale})
    crUsdc.mint(0, {"from": whale})
    strategy.harvest({"from": strategist})

    chain.sleep(6 * 3600 + 1)  # pass protection period
    chain.mine(1)

    whale_share = vault.balanceOf(whale)
    gov_share = vault.balanceOf(strategist)
    rew_share = vault.balanceOf(rewards)
    pending_rewards = vault.balanceOf(
        strategy
    )  # rewards pending to be claimed by rewards
    # add strategy return
    assert vault.totalSupply() == whale_share + gov_share + rew_share + pending_rewards
    value = vault.totalSupply() * vault.pricePerShare() / (10 ** decimals)
    assert (
        value * 0.99999 < vault.totalAssets() and value * 1.00001 > vault.totalAssets()
    )

    assert (
        value * 0.9999
        < (amount1 * 2)
        + vault.strategies(strategy)[7]  # changed from 6 to 7 (totalGains)
        and value * 1.0001 > (amount1 * 2) + vault.strategies(strategy)[7]  # see
    )
    # check we are within 0.1% of expected returns
    assert (
        value < strategy.estimatedTotalAssets() * 1.001
        and value > strategy.estimatedTotalAssets() * 0.999
    )

    assert gov_share == whale_share  # they deposited the same at the same moment


def test_apr(
    strategy,
    chain,
    vault,
    cUsdc,
    crUsdc,
    rewards,
    currency,
    gov,
    interface,
    whale,
    strategist,
    fn_isolation,
):
    decimals = currency.decimals()
    deposit_limit = 100_000_000 * 1e6
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 500, {"from": gov})
    vault.setDepositLimit(deposit_limit, {"from": gov})
    andre = whale
    gov = strategist
    amount1 = 50 * (10 ** decimals)
    currency.approve(vault, 2 ** 256 - 1, {"from": andre})
    currency.approve(vault, 2 ** 256 - 1, {"from": gov})

    amount2 = 50_000 * (10 ** decimals)

    vault.deposit(amount1, {"from": gov})
    vault.deposit(amount2, {"from": andre})

    strategy.harvest({"from": gov})  # invest deposited assets

    startingBalance = vault.totalAssets()

    for i in range(10):
        cUsdc.mint(0, {"from": whale})
        crUsdc.mint(0, {"from": whale})
        waitBlock = 25
        # print(f'\n----wait {waitBlock} blocks----')
        chain.mine(waitBlock)
        chain.sleep(25 * 13)
        # print(f'\n----harvest----')
        strategy.harvest({"from": strategist})

        # genericStateOfStrat(strategy, currency, vault)
        # genericStateOfVault(vault, currency)

        profit = (vault.totalAssets() - startingBalance) / 1e6
        strState = vault.strategies(strategy)
        totalReturns = strState[7]  # changed to new StrategyParams
        totaleth = totalReturns / 1e6
        # print(f'Real Profit: {profit:.5f}')
        difff = profit - totaleth
        # print(f'Diff: {difff}')

        blocks_per_year = 2_252_857
        assert startingBalance != 0
        time = (i + 1) * waitBlock
        assert time != 0
        apr = (totalReturns / startingBalance) * (blocks_per_year / time)
        assert apr > 0 and apr < 1
        # print(apr)
        print(f"implied apr: {apr:.8%}")

    vault.withdraw(vault.balanceOf(gov), {"from": gov})
    vault.withdraw(vault.balanceOf(andre), {"from": andre})


def test_manual_override(
    Strategy,
    chain,
    vault,
    cUsdc,
    crUsdc,
    rewards,
    currency,
    gov,
    GenericCompound,
    GenericCream,
    fn_isolation,
    GenericDyDx,
    interface,
    whale,
    strategist,
):
    strategy = strategist.deploy(Strategy, vault)
    decimals = currency.decimals()
    compoundPlugin = strategist.deploy(GenericCompound, strategy, "Compound", cUsdc)
    creamPlugin = strategist.deploy(GenericCream, strategy, "Cream", crUsdc)
    dydxPlugin = strategist.deploy(GenericDyDx, strategy, "DyDx")
    strategy.addLender(compoundPlugin, {"from": gov})
    assert strategy.numLenders() == 1
    strategy.addLender(creamPlugin, {"from": gov})
    assert strategy.numLenders() == 2
    strategy.addLender(dydxPlugin, {"from": gov})
    assert strategy.numLenders() == 3

    ecimals = currency.decimals()
    deposit_limit = 100_000_000 * (10 ** decimals)
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 500, {"from": gov})
    vault.setDepositLimit(deposit_limit, {"from": gov})
    andre = whale
    gov = strategist
    amount1 = 50 * (10 ** decimals)
    currency.approve(vault, 2 ** 256 - 1, {"from": andre})
    currency.approve(vault, 2 ** 256 - 1, {"from": gov})

    amount2 = 50_000 * (10 ** decimals)

    vault.deposit(amount1, {"from": gov})
    vault.deposit(amount2, {"from": andre})

    strategy.harvest({"from": gov})

    # at this stage only one strat has balance in it
    assert (
        (
            compoundPlugin.hasAssets() == False
            and dydxPlugin.hasAssets()
            and creamPlugin.hasAssets() == False
        )
        or (
            compoundPlugin.hasAssets()
            and dydxPlugin.hasAssets() == False
            and creamPlugin.hasAssets() == False
        )
        or (
            compoundPlugin.hasAssets() == False
            and dydxPlugin.hasAssets() == False
            and creamPlugin.hasAssets()
        )
    )

    manualAll = [[compoundPlugin, 500], [dydxPlugin, 250], [creamPlugin, 250]]
    strategy.manualAllocation(manualAll, {"from": gov})
    status = strategy.lendStatuses()
    assert (
        compoundPlugin.hasAssets()
        and dydxPlugin.hasAssets()
        and creamPlugin.hasAssets()
    )

    form = "{:.2%}"
    formS = "{:,.0f}"
    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e6)}, APR: {form.format(j[2]/1e18)}"
        )

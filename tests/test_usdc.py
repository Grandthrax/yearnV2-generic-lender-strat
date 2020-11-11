from itertools import count
from brownie import Wei, reverts
from useful_methods import  genericStateOfVault,genericStateOfStrat
import random
import brownie

def test_good_migration(usdc,Strategy, chain, whale,gov,strategist,rando,vault, strategy):
    currency = usdc

    usdc.approve(vault, 2 ** 256 - 1, {"from": whale} )
    usdc.approve(vault, 2 ** 256 - 1, {"from": strategist} )

    
    deposit_limit = 1_000_000_000 *1e6
    vault.addStrategy(strategy, deposit_limit, deposit_limit, 500, {"from": strategist})
    
    amount1 = 500 *1e6
    vault.deposit(amount1, {"from": whale})

    amount1 = 50 *1e6
    vault.deposit(amount1, {"from": strategist})
    gov= strategist

    strategy.harvest({'from': gov})
    chain.sleep(30*13)
    chain.mine(30)

    strategy.harvest({'from': gov})

    strategy_debt = vault.strategies(strategy)[4]  # totalDebt
    prior_position = strategy.estimatedTotalAssets()
    assert strategy_debt > 0

    new_strategy = strategist.deploy(Strategy, vault)
    assert vault.strategies(new_strategy)[4] == 0
    assert currency.balanceOf(new_strategy) == 0

    # Only Governance can migrate
    with brownie.reverts():
        vault.migrateStrategy(strategy, new_strategy, {"from": rando})

    vault.migrateStrategy(strategy, new_strategy, {"from": gov})
    assert vault.strategies(strategy)[4] == 0
    assert vault.strategies(new_strategy)[4] == strategy_debt
    assert new_strategy.estimatedTotalAssets() > prior_position*0.999 or new_strategy.estimatedTotalAssets() < prior_position*1.001

def test_normal_activity(usdc,Strategy, crUsdc,cUsdc, chain, whale,gov,strategist,rando,vault, strategy):
    starting_balance = usdc.balanceOf(strategist)
    currency = usdc
    decimals = currency.decimals()
    
    usdc.approve(vault, 2 ** 256 - 1, {"from": whale} )
    usdc.approve(vault, 2 ** 256 - 1, {"from": strategist} )
    
    deposit_limit = 1_000_000_000 *1e6
    vault.addStrategy(strategy, deposit_limit, deposit_limit, 500, {"from": strategist})

    
    #our humble strategist deposits some test funds
    depositAmount =  501 *1e6
    vault.deposit(depositAmount, {"from": strategist})

    assert strategy.estimatedTotalAssets() == 0
    assert strategy.harvestTrigger(1) == True

    strategy.harvest({"from": strategist})

    assert strategy.estimatedTotalAssets() >= depositAmount*0.999999 #losing some dust is ok
    assert strategy.harvestTrigger(1) == False

    #whale deposits as well
    whale_deposit  =100_000 *1e6
    vault.deposit(whale_deposit, {"from": whale})
    assert strategy.harvestTrigger(1000) == True
    strategy.harvest({"from": strategist})

    for i in range(15):
        waitBlock = random.randint(10,50)
        cUsdc.mint(0, {"from": whale})
        crUsdc.mint(0, {"from": whale})
        chain.mine(waitBlock)
        chain.sleep(15*30)

        strategy.harvest({"from": strategist})
        something= True
        action = random.randint(0,9)
        if action < 3:
            percent = random.randint(50,100)

            shareprice = vault.pricePerShare()
            
            shares = vault.balanceOf(whale)
            sharesout = shares*percent/100
            expectedout = sharesout*(shareprice/1e18)*(10 ** (decimals*2))
            balanceBefore = currency.balanceOf(whale)

            vault.withdraw(sharesout, {'from': whale})
            balanceAfter = currency.balanceOf(whale)
            withdrawn = balanceAfter - balanceBefore
            assert withdrawn > expectedout*0.99 and withdrawn < expectedout*1.01

       
        elif action < 5:
            depositAm = random.randint(10,100) * (10 ** decimals)
            vault.deposit(depositAm, {"from": whale})

    #strategist withdraws
    shareprice = vault.pricePerShare()
            
    shares = vault.balanceOf(strategist)
    expectedout = shares*(shareprice/1e18)*(10 ** (decimals*2))
    balanceBefore = currency.balanceOf(strategist)
    vault.withdraw(vault.balanceOf(strategist), {'from': strategist})
    balanceAfter = currency.balanceOf(strategist)
    withdrawn = balanceAfter - balanceBefore
    assert withdrawn > expectedout*0.99 and withdrawn < expectedout*1.01

    profit = balanceAfter- starting_balance
    assert profit > 0
    print(profit)



def test_debt_increase(usdc,Strategy, chain, whale,gov,strategist,rando,vault, strategy):

    currency = usdc
    usdc.approve(vault, 2 ** 256 - 1, {"from": whale} )

    
    deposit_limit = 100_000_000 *1e6
    vault.addStrategy(strategy, deposit_limit, deposit_limit, 500, {"from": gov})


    form = "{:.2%}"
    formS = "{:,.0f}"
    firstDeposit = 2000_000 *1e6
    predictedApr = strategy.estimatedFutureAPR(firstDeposit)
    print(f"Predicted APR from {formS.format(firstDeposit/1e6)} deposit: {form.format(predictedApr/1e18)}")
    vault.deposit(firstDeposit, {"from": whale})
    print("Deposit: ", formS.format(firstDeposit/1e6))
    strategy.harvest({"from": strategist})
    realApr = strategy.estimatedAPR()
    print("Current APR: ", form.format(realApr/1e18))
    status = strategy.lendStatuses()
    
    for j in status:
        print(f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e6)}, APR: {form.format(j[2]/1e18)}")
    
    assert realApr > predictedApr*.999 and realApr <  predictedApr*1.001
    
    predictedApr = strategy.estimatedFutureAPR(firstDeposit*2)
    print(f"\nPredicted APR from {formS.format(firstDeposit/1e6)} deposit: {form.format(predictedApr/1e18)}")
    print("Deposit: ", formS.format(firstDeposit/1e6))
    vault.deposit(firstDeposit, {"from": whale})

    strategy.harvest({"from": strategist})
    realApr = strategy.estimatedAPR()
   
    print(f"Real APR after deposit: {form.format(realApr/1e18)}")
    status = strategy.lendStatuses()
        
    for j in status:
        print(f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e6)}, APR: {form.format(j[2]/1e18)}")
    assert realApr > predictedApr*.999 and realApr <  predictedApr*1.001
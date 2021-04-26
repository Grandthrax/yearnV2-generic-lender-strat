from itertools import count
from brownie import Wei, reverts, Contract, interface
from useful_methods import genericStateOfVault, genericStateOfStrat
import random
import brownie
executor_abi = [{"inputs":[{"internalType":"address","name":"governanceStrategy","type":"address"},{"internalType":"uint256","name":"votingDelay","type":"uint256"},{"internalType":"address","name":"guardian","type":"address"},{"internalType":"address[]","name":"executors","type":"address[]"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"address","name":"executor","type":"address"}],"name":"ExecutorAuthorized","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"address","name":"executor","type":"address"}],"name":"ExecutorUnauthorized","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"newStrategy","type":"address"},{"indexed":True,"internalType":"address","name":"initiatorChange","type":"address"}],"name":"GovernanceStrategyChanged","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":True,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"uint256","name":"id","type":"uint256"}],"name":"ProposalCanceled","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"uint256","name":"id","type":"uint256"},{"indexed":True,"internalType":"address","name":"creator","type":"address"},{"indexed":True,"internalType":"contract IExecutorWithTimelock","name":"executor","type":"address"},{"indexed":False,"internalType":"address[]","name":"targets","type":"address[]"},{"indexed":False,"internalType":"uint256[]","name":"values","type":"uint256[]"},{"indexed":False,"internalType":"string[]","name":"signatures","type":"string[]"},{"indexed":False,"internalType":"bytes[]","name":"calldatas","type":"bytes[]"},{"indexed":False,"internalType":"bool[]","name":"withDelegatecalls","type":"bool[]"},{"indexed":False,"internalType":"uint256","name":"startBlock","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"endBlock","type":"uint256"},{"indexed":False,"internalType":"address","name":"strategy","type":"address"},{"indexed":False,"internalType":"bytes32","name":"ipfsHash","type":"bytes32"}],"name":"ProposalCreated","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"uint256","name":"id","type":"uint256"},{"indexed":True,"internalType":"address","name":"initiatorExecution","type":"address"}],"name":"ProposalExecuted","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"uint256","name":"id","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"executionTime","type":"uint256"},{"indexed":True,"internalType":"address","name":"initiatorQueueing","type":"address"}],"name":"ProposalQueued","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"uint256","name":"id","type":"uint256"},{"indexed":True,"internalType":"address","name":"voter","type":"address"},{"indexed":False,"internalType":"bool","name":"support","type":"bool"},{"indexed":False,"internalType":"uint256","name":"votingPower","type":"uint256"}],"name":"VoteEmitted","type":"event"},{"anonymous":False,"inputs":[{"indexed":False,"internalType":"uint256","name":"newVotingDelay","type":"uint256"},{"indexed":True,"internalType":"address","name":"initiatorChange","type":"address"}],"name":"VotingDelayChanged","type":"event"},{"inputs":[],"name":"DOMAIN_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"NAME","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"VOTE_EMITTED_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"__abdicate","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address[]","name":"executors","type":"address[]"}],"name":"authorizeExecutors","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"proposalId","type":"uint256"}],"name":"cancel","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"contract IExecutorWithTimelock","name":"executor","type":"address"},{"internalType":"address[]","name":"targets","type":"address[]"},{"internalType":"uint256[]","name":"values","type":"uint256[]"},{"internalType":"string[]","name":"signatures","type":"string[]"},{"internalType":"bytes[]","name":"calldatas","type":"bytes[]"},{"internalType":"bool[]","name":"withDelegatecalls","type":"bool[]"},{"internalType":"bytes32","name":"ipfsHash","type":"bytes32"}],"name":"create","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"proposalId","type":"uint256"}],"name":"execute","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"getGovernanceStrategy","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getGuardian","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"proposalId","type":"uint256"}],"name":"getProposalById","outputs":[{"components":[{"internalType":"uint256","name":"id","type":"uint256"},{"internalType":"address","name":"creator","type":"address"},{"internalType":"contract IExecutorWithTimelock","name":"executor","type":"address"},{"internalType":"address[]","name":"targets","type":"address[]"},{"internalType":"uint256[]","name":"values","type":"uint256[]"},{"internalType":"string[]","name":"signatures","type":"string[]"},{"internalType":"bytes[]","name":"calldatas","type":"bytes[]"},{"internalType":"bool[]","name":"withDelegatecalls","type":"bool[]"},{"internalType":"uint256","name":"startBlock","type":"uint256"},{"internalType":"uint256","name":"endBlock","type":"uint256"},{"internalType":"uint256","name":"executionTime","type":"uint256"},{"internalType":"uint256","name":"forVotes","type":"uint256"},{"internalType":"uint256","name":"againstVotes","type":"uint256"},{"internalType":"bool","name":"executed","type":"bool"},{"internalType":"bool","name":"canceled","type":"bool"},{"internalType":"address","name":"strategy","type":"address"},{"internalType":"bytes32","name":"ipfsHash","type":"bytes32"}],"internalType":"struct IAaveGovernanceV2.ProposalWithoutVotes","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"proposalId","type":"uint256"}],"name":"getProposalState","outputs":[{"internalType":"enum IAaveGovernanceV2.ProposalState","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getProposalsCount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"proposalId","type":"uint256"},{"internalType":"address","name":"voter","type":"address"}],"name":"getVoteOnProposal","outputs":[{"components":[{"internalType":"bool","name":"support","type":"bool"},{"internalType":"uint248","name":"votingPower","type":"uint248"}],"internalType":"struct IAaveGovernanceV2.Vote","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getVotingDelay","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"executor","type":"address"}],"name":"isExecutorAuthorized","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"proposalId","type":"uint256"}],"name":"queue","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"governanceStrategy","type":"address"}],"name":"setGovernanceStrategy","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"votingDelay","type":"uint256"}],"name":"setVotingDelay","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"proposalId","type":"uint256"},{"internalType":"bool","name":"support","type":"bool"}],"name":"submitVote","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"proposalId","type":"uint256"},{"internalType":"bool","name":"support","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"submitVoteBySignature","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address[]","name":"executors","type":"address[]"}],"name":"unauthorizeExecutors","outputs":[],"stateMutability":"nonpayable","type":"function"}]

def test_aave_rewards(chain,
    usdc,
    whale,
    gov,
    strategist,
    rando,
    vault,
    Strategy,
    strategy,
    GenericAave,
    aUsdc):
    # Clone magic
    tx = strategy.clone(vault)
    cloned_strategy = Strategy.at(tx.return_value)
    cloned_strategy.setWithdrawalThreshold(
        strategy.withdrawalThreshold(), {"from": gov}
    )
    cloned_strategy.setDebtThreshold(strategy.debtThreshold(), {"from": gov})
    cloned_strategy.setProfitFactor(strategy.profitFactor(), {"from": gov})
    cloned_strategy.setMaxReportDelay(strategy.maxReportDelay(), {"from": gov})

    assert cloned_strategy.numLenders() == 0

    # Clone the aave lender
    original_aave = GenericAave.at(strategy.lenders(strategy.numLenders() - 1))
    tx = original_aave.cloneAaveLender(
        cloned_strategy, "ClonedAaveUSDC", aUsdc, False, {"from": gov}
    )
    cloned_lender = GenericAave.at(tx.return_value)
    assert cloned_lender.lenderName() == "ClonedAaveUSDC"

    cloned_strategy.addLender(cloned_lender, {"from": gov})
    starting_balance = usdc.balanceOf(strategist)
    currency = usdc
    decimals = currency.decimals()

    usdc.approve(vault, 2 ** 256 - 1, {"from": whale})
    usdc.approve(vault, 2 ** 256 - 1, {"from": strategist})

    deposit_limit = 1_000_000_000 * (10 ** (decimals))
    debt_ratio = 10_000
    vault.addStrategy(cloned_strategy, debt_ratio, 0, 2 ** 256 - 1, 500, {"from": gov})
    vault.setDepositLimit(deposit_limit, {"from": gov})

    assert deposit_limit == vault.depositLimit()

    # ------------------ set up proposal ------------------

    # chain.sleep(12 * 3600) # to be able to execute
    # chain.mine(1)
    # print("executing proposal 11") # to be able to test before the proposal is executed
    # executor = Contract.from_abi("AaveGovernanceV2", "0xec568fffba86c094cf06b22134b23074dfe2252c", executor_abi, owner="0x30fe242a69d7694a931791429815db792e24cf97")
    # tx = executor.execute(11)

    incentives_controller = Contract(aUsdc.getIncentivesController())
    assert incentives_controller.getDistributionEnd() > 0
    # ------------------ test starts ------------------
    # turning on claiming incentives logic
    cloned_lender.setIsIncentivised(True, {'from': strategist})

    # our humble strategist deposits some test funds
    depositAmount = 50000 * (10 ** (decimals))
    vault.deposit(depositAmount, {"from": strategist})

    assert cloned_strategy.estimatedTotalAssets() == 0
    chain.mine(1)
    assert cloned_strategy.harvestTrigger(1) == True

    cloned_strategy.harvest({"from": strategist})

    assert (
        cloned_strategy.estimatedTotalAssets() >= depositAmount * 0.999999
    )  # losing some dust is ok

    assert cloned_strategy.harvestTrigger(1) == False
    
    assert cloned_lender.harvestTrigger(1) == True # first harvest
    
    with brownie.reverts():## should fail for any non-management account
        cloned_lender.harvest({'from': whale})

    with brownie.reverts(): ## not in management so should revert
        cloned_lender.setKeep3r(whale, {'from': whale})

    cloned_lender.setKeep3r(whale, {'from': strategist})

    cloned_lender.harvest({'from': whale})

    assert cloned_lender.harvestTrigger(1) == False

    chain.sleep(10*3600*24+1) # we wait 10 days for the cooldown period 
    chain.mine(1)

    assert cloned_lender.harvestTrigger(1) == True
    assert incentives_controller.getRewardsBalance([aUsdc], cloned_lender) > 0
    previousBalance = aUsdc.balanceOf(cloned_lender)
    
    cloned_lender.harvest({'from': strategist}) # redeem staked tokens, sell them, deposit them, claim rewards

    assert incentives_controller.getRewardsBalance([aUsdc], cloned_lender) == 0
    assert aUsdc.balanceOf(cloned_lender) > previousBalance # deposit sold rewards

    cloned_strategy.harvest({'from': strategist})
    
    status = cloned_strategy.lendStatuses()
    form = "{:.2%}"
    formS = "{:,.0f}"
    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e6)}, APR: {form.format(j[2]/1e18)}"
        )
    chain.sleep(6*3600)
    chain.mine(1)
    vault.withdraw({"from": strategist})

def test_no_emissions(
    chain,
    usdc,
    whale,
    gov,
    strategist,
    rando,
    vault,
    Strategy,
    strategy,
    GenericAave,
    aUsdc):
    # Clone magic
    vault = Contract("0xa5cA62D95D24A4a350983D5B8ac4EB8638887396")# using SUSD vault (it is not in the LP program)
    
    tx = strategy.clone(vault) 
    cloned_strategy = Strategy.at(tx.return_value)
    cloned_strategy.setWithdrawalThreshold(
        strategy.withdrawalThreshold(), {"from": vault.governance()}
    )
    cloned_strategy.setDebtThreshold(strategy.debtThreshold(), {"from": vault.governance()})
    cloned_strategy.setProfitFactor(strategy.profitFactor(), {"from": vault.governance()})
    cloned_strategy.setMaxReportDelay(strategy.maxReportDelay(), {"from": vault.governance()})

    assert cloned_strategy.numLenders() == 0
    aSUSD = interface.IAToken("0x6c5024cd4f8a59110119c56f8933403a539555eb")# aSUSD
    # Clone the aave lender
    original_aave = GenericAave.at(strategy.lenders(strategy.numLenders() - 1))
    tx = original_aave.cloneAaveLender(
        cloned_strategy, "ClonedAaveSUSD", aSUSD, False, {"from": vault.governance()} 
    )
    cloned_lender = GenericAave.at(tx.return_value)
    assert cloned_lender.lenderName() == "ClonedAaveSUSD"

    cloned_strategy.addLender(cloned_lender, {"from": vault.governance()})
    currency = interface.ERC20("0x57ab1ec28d129707052df4df418d58a2d46d5f51") #sUSD
    susd_whale = "0x49be88f0fcc3a8393a59d3688480d7d253c37d2a"
    currency.transfer(strategist, 100e18, {'from': susd_whale})
    starting_balance = currency.balanceOf(strategist)

    decimals = currency.decimals()

    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    currency.approve(vault, 2 ** 256 - 1, {"from": strategist})

    deposit_limit = 1_000_000_000 * (10 ** (decimals))
    debt_ratio = 10_000
    vault.updateStrategyDebtRatio(vault.withdrawalQueue(0), 0, {'from': vault.governance()})
    vault.updateStrategyDebtRatio(vault.withdrawalQueue(1), 0, {'from': vault.governance()})
    vault.addStrategy(cloned_strategy, debt_ratio, 0, 2 ** 256 - 1, 500, {"from": vault.governance()})
    vault.setDepositLimit(deposit_limit, {"from": vault.governance()})

    assert deposit_limit == vault.depositLimit()
    with brownie.reverts():
        cloned_lender.setIsIncentivised(True, {'from': strategist})
    # ------------------ set up proposal ------------------

    # chain.sleep(12 * 3600) # to be able to execute
    # chain.mine(1)
    # print("executing proposal 11") # to be able to test before the proposal is executed
    # executor = Contract.from_abi("AaveGovernanceV2", "0xec568fffba86c094cf06b22134b23074dfe2252c", executor_abi, owner="0x30fe242a69d7694a931791429815db792e24cf97")
    # tx = executor.execute(11)

    # should fail because sUSD is not incentivised
    with brownie.reverts():
        cloned_lender.setIsIncentivised(True, {'from': strategist})
# our humble strategist deposits some test funds
    depositAmount = 50 * (10 ** (decimals))
    vault.deposit(depositAmount, {"from": strategist})

    assert cloned_strategy.estimatedTotalAssets() == 0
    chain.mine(1)
    assert cloned_strategy.harvestTrigger(1) == True

    cloned_strategy.harvest({"from": strategist})

    assert (
        cloned_strategy.estimatedTotalAssets() >= depositAmount * 0.999999
    )  # losing some dust is ok

    assert cloned_strategy.harvestTrigger(1) == False
    
    assert cloned_lender.harvestTrigger(1) == False # harvest is unavailable
    
    with brownie.reverts():
        cloned_lender.harvest({'from': strategist}) # if called, it does not revert

    assert cloned_lender.harvestTrigger(1) == False

    chain.sleep(10*3600*24+1) # we wait 10 days for the cooldown period 
    chain.mine(1)

    assert cloned_lender.harvestTrigger(1) == False # always unavailable

    cloned_strategy.harvest({'from': strategist})
    chain.sleep(6*3600)
    chain.mine(1)
    vault.withdraw({"from": strategist})

import pytest
from brownie import Wei, reverts
import brownie


@pytest.mark.require_network("mainnet-fork")
def test_leveraged(chain, vault, gov, whale, weth, leverager, strategy):
    weth.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(Wei("1 ether"), {"from": whale})
    leverager.harvest({"from": gov})

    previousAssets = strategy.estimatedTotalAssets()
    chain.sleep(86400 * 10)
    chain.mine(1)

    assert previousAssets < strategy.estimatedTotalAssets()
    t = leverager.harvest({"from": gov})

    assert vault.strategies(leverager).dict()["totalGain"] > 0

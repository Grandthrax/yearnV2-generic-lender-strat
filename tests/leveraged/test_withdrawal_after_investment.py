import pytest
from brownie import Wei, reverts
import brownie


@pytest.mark.require_network("mainnet-fork")
def test_withdrawal_after_investment(
    chain, vault, gov, whale, weth, leverager, strategy
):
    whaleInitialbalance = weth.balanceOf(whale)

    weth.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(Wei("1 ether"), {"from": whale})
    leverager.harvest({"from": gov})

    chain.sleep(86400 * 10)
    chain.mine(1)

    leverager.harvest({"from": gov})

    vault.withdraw({"from": whale})
    assert whaleInitialbalance < weth.balanceOf(whale)

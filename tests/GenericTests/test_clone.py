import pytest
import brownie

from brownie import Wei


def test_clone(gov, vault, keeper, strategy, strategist, Strategy):

    # Do the regular add strategy with the regular one
    vault.setDepositLimit(Wei("1000000 ether"), {"from": gov})
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 1_000, {"from": gov})

    # Switch rewards with keeper to make sure the proxy worked
    tx = strategy.clone(vault, strategist, keeper, strategist)
    new_strategy = Strategy.at(tx.return_value)

    # Check that we have the same thing but with keeper/rewards switched
    assert new_strategy.keeper() != new_strategy.rewards()
    assert strategy.keeper() == new_strategy.rewards()
    assert strategy.rewards() == new_strategy.keeper()

    # Migrate to the new proxied strategy
    vault.migrateStrategy(strategy, new_strategy, {"from": gov})


def test_double_initialize(gov, vault, strategy, Strategy):

    # Switch rewards with keeper to make sure the proxy worked
    tx = strategy.clone(vault, gov, gov, gov)
    new_strategy = Strategy.at(tx.return_value)

    with brownie.reverts():
        new_strategy.initialize(vault, gov, gov, gov, {"from": gov})

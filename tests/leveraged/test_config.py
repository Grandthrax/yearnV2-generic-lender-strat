import pytest
from brownie import Wei, reverts
import brownie


@pytest.mark.require_network("mainnet-fork")
def test_config(leverager, strategy):
    assert leverager.name() == "LeveragedEth"
    assert strategy.name() == "HomoraStrategy"

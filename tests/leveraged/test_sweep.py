import pytest
import brownie


@pytest.mark.require_network("mainnet-fork")
def test_sweep(leverager, gov):
    # want
    with brownie.reverts():
        leverager.sweep("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", {"from": gov})

    # cyETH
    with brownie.reverts():
        leverager.sweep("0x41c84c0e2EE0b740Cf0d31F63f3B6F627DC6b393", {"from": gov})

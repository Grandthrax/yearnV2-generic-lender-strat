from itertools import count
from brownie import Wei, reverts
from useful_methods import genericStateOfStrat, genericStateOfVault, deposit, sleep
import random


def test_wbtc_add_compound_live(
    currency,
    interface,
    samdev,
    Contract,
    devychad,
    live_strat_wbtc,
    live_vault_wbtc
    chain,
    whale,
    gov,
    rando,
    fn_isolation,
):
from itertools import count
from brownie import Wei, reverts
from useful_methods import genericStateOfVault, genericStateOfStrat
import random
import brownie


def xtest_live_py(
    currency,
    live_GenericCompound_usdc_1,
    live_GenericCream_usdc_1,
    live_GenericDyDx_usdc_1,
    live_vault_usdc,
    live_strat_usdc_1,
    Strategy,
    samdev,
):
    vault = live_vault_usdc
    # old_str = Strategy.at('0xe3a0f5aF6B213b9A926fd611Ca8F117FC6fEb756')

    # genericStateOfStrat(old_str, currency, vault)
    # genericStateOfVault(vault, currency)

    form = "{:.2%}"
    formS = "{:,.0f}"
    # status = live_strat_usdc_1.lendStatuses()
    # for j in status:
    #    print(f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e6)}, APR: {form.format(j[2]/1e18)}")

    # vault.migrateStrategy(old_str, live_strat_usdc_1, {'from': samdev})
    # live_strat_usdc_1.harvest({'from': samdev})

    # genericStateOfStrat(old_str, currency, vault)
    # genericStateOfVault(vault, currency)
    # genericStateOfStrat(live_strat_usdc_1, currency, vault)
    # genericStateOfVault(vault, currency)
    status = live_strat_usdc_1.lendStatuses()
    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e6)}, APR: {form.format(j[2]/1e18)}"
        )

    live_strat_usdc_1.tend({"from": samdev})
    status = live_strat_usdc_1.lendStatuses()
    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e6)}, APR: {form.format(j[2]/1e18)}"
        )

from pathlib import Path
import yaml

from brownie import interface, accounts, network, web3, Wei, config
from eth_utils import is_checksum_address

    
Vault = project.load(
    Path.home() / ".brownie" / "packages" / config["dependencies"][0]
).Vault

def get_address(msg: str) -> str:
    while True:
        val = input(msg)
        if is_checksum_address(val):
            return val
        else:
            addr = web3.ens.address(val)
            if addr:
                print(f"Found ENS '{val}' [{addr}]")
                return addr
        print(f"I'm sorry, but '{val}' is not a checksummed address or ENS")


def main():

    print(f"You are using the '{network.show_active()}' network")
    account_name = input(f"What account to use?: ")
    dev = accounts.load(account_name)
    print(f"You are using: 'dev' [{dev.address}]")
    token = interface.ERC20(get_address("ERC20 Token: "))
    #token = Token.at("0x6B175474E89094C44Da98b954EedeAC495271d0F")
    #gov = get_address("yEarn Governance: ")
    gov = dev
    #rewards = get_address("Rewards contract: ")
    rewards = dev
    #name = input(f"Set description ['yearn {token.name()}']: ") or ""
    name = "WETH yVault"
    #symbol = input(f"Set symbol ['y{token.symbol()}']: ") or ""
    symbol = 'yvWETH'
    print(
        f"""
    Vault Parameters

     token: {token.address}
  governer: {gov}
   rewards: {rewards}
      name: '{name or 'yearn ' + token.name()}'
    symbol: '{symbol or 'y' + token.symbol()}'
    """
    )
    if input("Deploy New Vault? y/[N]: ").lower() != "y":
        return
    print("Deploying Vault...")
    vault = Vault.deploy(token, gov, rewards, name, symbol,  {'from': dev, 'gas_price':Wei("35 gwei")})
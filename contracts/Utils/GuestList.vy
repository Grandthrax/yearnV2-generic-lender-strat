# @version 0.2.7
from vyper.interfaces import ERC20

bouncer: public(address)
guests: public(HashMap[address, bool])
tokens: public(address[10])
amounts: public(uint256[10])


@external
def __init__():
    self.bouncer = msg.sender


@external
def set_guests(guest: address[20], invited: bool[20]):
    """
    Invite of kick guests from the party.
    """
    assert msg.sender == self.bouncer
    for i in range(20):
        if guest[i] == ZERO_ADDRESS:
            break
        self.guests[guest[i]] = invited[i]


@external
def set_permits(_tokens: address[10], _amounts: uint256[10]):
    """
    Set tokens and min amounts which guarantee entrance.
    """
    assert msg.sender == self.bouncer
    self.tokens = _tokens
    self.amounts = _amounts


@external
def set_bouncer(new_bouncer: address):
    """
    Replace bouncer role.
    """
    assert msg.sender == self.bouncer
    self.bouncer = new_bouncer


@view
@external
def authorized(guest: address, amount: uint256) -> bool:
    """
    Check if a user with a bag of certain size is allowed to the party.
    """
    if self.guests[guest]:
        return True
    for i in range(10):
        if self.tokens[i] == ZERO_ADDRESS:
            break
        if ERC20(self.tokens[i]).balanceOf(guest) >= self.amounts[i]:
            return True
    return False
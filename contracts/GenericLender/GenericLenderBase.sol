pragma solidity 0.6.12;

import "@yearnvaults/contracts/BaseStrategy.sol";
import "@openzeppelinV3/contracts/token/ERC20/IERC20.sol";
import "@openzeppelinV3/contracts/math/SafeMath.sol";

import "./IGenericLender.sol";

abstract contract GenericLenderBase is IGenericLender {
    VaultAPI public vault;
    BaseStrategy public strategy;
    IERC20 public want;
    string public override lenderName;

    uint256 public dust;

    constructor(address _strategy, string memory name) public {
        strategy = BaseStrategy(_strategy);
        vault = VaultAPI(strategy.vault());
        want = IERC20(vault.token());
        lenderName = name;
        dust = 10000;

        want.approve(_strategy, uint256(-1));
    }

    function setDust(uint256 _dust) external override virtual management {
        dust = _dust;
    }

    function sweep(address _token) external override virtual management {
        address[] memory _protectedTokens = protectedTokens();
        for (uint256 i; i < _protectedTokens.length; i++) require(_token != _protectedTokens[i], "!protected");

        IERC20(_token).transfer(vault.governance(), IERC20(_token).balanceOf(address(this)));
    }

    function protectedTokens() internal view virtual returns (address[] memory);

    //make sure to use
    modifier management() {
        require(msg.sender == address(strategy) || msg.sender == vault.governance() || msg.sender == strategy.strategist(), "!management");
        _;
    }
}

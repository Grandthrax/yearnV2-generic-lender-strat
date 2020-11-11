pragma solidity 0.6.12;

import "@yearnvaults/contracts/BaseStrategy.sol";
import "@openzeppelinV3/contracts/token/ERC20/IERC20.sol";
import "@openzeppelinV3/contracts/math/SafeMath.sol";

abstract contract IGenericLender {
    

    VaultAPI public vault;
    BaseStrategy public strategy;
    IERC20 public want;
    string public lenderName;

    constructor(address _strategy, string memory name) public {
        strategy = BaseStrategy(_strategy);
        vault = VaultAPI(strategy.vault());
        want = IERC20(vault.token());
        lenderName = name;
        
        want.approve(_strategy, uint256(-1));

    }

    function nav() external virtual view  returns (uint256);
    function apr() external virtual view  returns (uint256);
    function weightedApr() external virtual view  returns (uint256);
    function withdraw(uint256 amount) external virtual  returns (uint256);
    function emergencyWithdraw(uint256 amount) external virtual;
    function deposit() external virtual;
    function withdrawAll() external virtual returns (bool);
    function enabled() external virtual view returns (bool);
    function hasAssets() external virtual view returns (bool);
    function aprAfterDeposit(uint256 amount) external virtual view returns (uint256);


    function sweep(address _token) external management {
        address[] memory _protectedTokens = protectedTokens();
        for (uint256 i; i < _protectedTokens.length; i++) require(_token != _protectedTokens[i], "!protected");

        IERC20(_token).transfer(vault.governance(), IERC20(_token).balanceOf(address(this)));
    }
    function protectedTokens() internal virtual view returns (address[] memory);

    

    //make sure to use
    modifier management(){
        require(msg.sender == address(strategy) ||
        msg.sender == vault.governance() || msg.sender == strategy.strategist(), "!management");
        _;
    }
}

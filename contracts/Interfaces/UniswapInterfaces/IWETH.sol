pragma solidity >=0.5.0;
import "@openzeppelinV3/contracts/token/ERC20/IERC20.sol";

interface IWETH is IERC20 {
    function deposit() external payable;

    function decimals() external view returns (uint256);

    function withdraw(uint256) external;
}

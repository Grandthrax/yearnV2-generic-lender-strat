pragma solidity >=0.5.0;

interface PriceOracle {
    function getUnderlyingPrice(address ctoken) external view returns (uint256);
}

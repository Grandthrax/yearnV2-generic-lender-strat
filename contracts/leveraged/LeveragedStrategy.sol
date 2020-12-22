// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.6.12;

interface LeveragedStrategy {
    function name() external pure returns (string memory);

    function apr() external view returns (uint256);

    function estimatedTotalAssets() external view returns (uint256);

    function prepareReturn(uint256, uint256)
        external
        returns (
            uint256 _profit,
            uint256 _loss,
            uint256 _debtPayment
        );

    function adjustPosition(uint256) external;

    function liquidatePosition(uint256) external returns (uint256 _amountFreed);

    function prepareMigration(address) external;

    function protectedTokens() external view returns (address[] memory);
}

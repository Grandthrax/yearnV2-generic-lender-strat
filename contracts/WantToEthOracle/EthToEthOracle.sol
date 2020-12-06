pragma solidity 0.6.12;

import './IWantToEth.sol';

contract EthToEthOracle is IWantToEth {
    function wantToEth(uint256 input) external override view returns (uint256){
        return input;
    }

    function ethToWant(uint256 input) external override view returns (uint256){
        return input;
    }
}
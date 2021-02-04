// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

import "./GenericLenderBase.sol";
import "../Interfaces/Aave/IAToken.sol";
import "../Interfaces/Aave/ILendingPool.sol";
import "../Interfaces/Aave/IProtocolDataProvider.sol";
import "../Interfaces/Aave/IReserveInterestRateStrategy.sol";
import "../Libraries/Aave/DataTypes.sol";

/********************
 *   A lender plugin for LenderYieldOptimiser for any erc20 asset on Aave (not eth)
 *   Made by SamPriestley.com
 *   https://github.com/Grandthrax/yearnv2/blob/master/contracts/GenericLender/GenericCream.sol
 *
 ********************* */

contract GenericAave is GenericLenderBase {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;
    
    IProtocolDataProvider public immutable protocolDataProvider;
    IAToken public immutable aToken;

    constructor(
        address _strategy,
        string memory name,
        IProtocolDataProvider _protocolDataProvider,
        IAToken _aToken
    ) public GenericLenderBase(_strategy, name) {
        protocolDataProvider = _protocolDataProvider;
        aToken = _aToken;

        require(ILendingPool(_protocolDataProvider.ADDRESSES_PROVIDER().getLendingPool()).getReserveData(address(want)).aTokenAddress == address(_aToken), "WRONG ATOKEN");

        want.approve(address(_protocolDataProvider.ADDRESSES_PROVIDER().getLendingPool()), type(uint256).max);
    }

    function nav() external view override returns (uint256) {
        return _nav();
    }

    function _nav() internal view returns (uint256) {
        return want.balanceOf(address(this)).add(underlyingBalanceStored());
    }

    function underlyingBalanceStored() public view returns (uint256 balance) {
        balance = aToken.balanceOf(address(this));
    }

    function apr() external view override returns (uint256) {
        return _apr();
    }

    function _apr() internal view returns (uint256) {
        return uint(_lendingPool().getReserveData(address(want)).currentLiquidityRate).div(1e9); // dividing by 1e9 to pass from ray to wad
    }

    function weightedApr() external view override returns (uint256) {
        uint256 a = _apr();
        return a.mul(_nav());
    }

    function withdraw(uint256 amount) external override management returns (uint256) {
        return _withdraw(amount);
    }

    //emergency withdraw. sends balance plus amount to governance
    function emergencyWithdraw(uint256 amount) external override management {
        _lendingPool().withdraw(address(want), amount, address(this));

        want.safeTransfer(vault.governance(), want.balanceOf(address(this)));
    }

    //withdraw an amount including any want balance
    function _withdraw(uint256 amount) internal returns (uint256) {
        uint256 balanceUnderlying = aToken.balanceOf(address(this));
        uint256 looseBalance = want.balanceOf(address(this));
        uint256 total = balanceUnderlying.add(looseBalance);

        if (amount > total) {
            //cant withdraw more than we own
            amount = total;
        }

        if (looseBalance >= amount) {
            want.safeTransfer(address(strategy), amount);
            return amount;
        }

        //not state changing but OK because of previous call
        uint256 liquidity = want.balanceOf(address(aToken));

        if (liquidity > 1) {
            uint256 toWithdraw = amount.sub(looseBalance);

            if (toWithdraw <= liquidity) {
                //we can take all
                _lendingPool().withdraw(address(want), toWithdraw, address(this));
            } else {
                //take all we can
                _lendingPool().withdraw(address(want), liquidity, address(this));
            }
        }
        looseBalance = want.balanceOf(address(this));
        want.safeTransfer(address(strategy), looseBalance);
        return looseBalance;
    }

    function deposit() external override management {
        uint256 balance = want.balanceOf(address(this));
        _lendingPool().deposit(address(want), balance, address(this), 7);
    }

    function withdrawAll() external override management returns (bool) {
        uint256 invested = _nav();
        uint256 returned = _withdraw(invested);
        return returned >= invested;
    }

    function hasAssets() external view override returns (bool) {
        return aToken.balanceOf(address(this)) > 0;
    }

    function _lendingPool() internal view returns (ILendingPool lendingPool) {
        lendingPool = ILendingPool(protocolDataProvider.ADDRESSES_PROVIDER().getLendingPool());
    }

    function aprAfterDeposit(uint256 extraAmount) external view override returns (uint256) {
        // i need to calculate new supplyRate after Deposit (when deposit has not been done yet)
        DataTypes.ReserveData memory reserveData = _lendingPool().getReserveData(address(want));

        (
            uint availableLiquidity,
            uint totalStableDebt,
            uint totalVariableDebt,
            ,
            ,
            ,
            uint averageStableBorrowRate,
            ,
            ,
            ) = protocolDataProvider.getReserveData(address(want));

        uint newLiquidity = availableLiquidity.add(extraAmount);

        (, , , , uint reserveFactor, , , , , ) = protocolDataProvider.getReserveConfigurationData(address(want));

        (uint newLiquidityRate, , ) = IReserveInterestRateStrategy(reserveData.interestRateStrategyAddress).calculateInterestRates(
            address(want),
            newLiquidity,
            totalStableDebt,
            totalVariableDebt,
            averageStableBorrowRate,
            reserveFactor
        );

        return newLiquidityRate.div(1e9); // divided by 1e9 to go from Ray to Wad
    }

    function protectedTokens() internal view override returns (address[] memory) {
        address[] memory protected = new address[](2);
        protected[0] = address(want);
        protected[1] = address(aToken);
        return protected;
    }
}

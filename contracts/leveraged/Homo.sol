// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.6.12;
pragma experimental ABIEncoderV2;

import "@openzeppelinV3/contracts/token/ERC20/IERC20.sol";
import "@openzeppelinV3/contracts/math/SafeMath.sol";
import "@openzeppelinV3/contracts/math/Math.sol";
import "@openzeppelinV3/contracts/utils/Address.sol";
import "@openzeppelinV3/contracts/token/ERC20/SafeERC20.sol";

import "@yearnvaults/contracts/BaseStrategy.sol";
import "../Interfaces/alpha-homora/Bank.sol";
import "../Interfaces/alpha-homora/BankConfig.sol";
import "../Interfaces/UniswapInterfaces/IWETH.sol";

import "./LeveragedStrategy.sol";

contract Homo is LeveragedStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    uint256 private constant secondsPerYear = 31556952;
    address public constant weth = address(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2);
    address public constant bank = address(0x67B66C99D3Eb37Fa76Aa3Ed1ff33E8e39F0b9c7A);
    IERC20 public constant want = IERC20(weth);
    address public leverager;

    modifier only(address caller) {
        require(msg.sender == address(caller));
        _;
    }

    constructor(address _leverager) public {
        leverager = _leverager;
        want.approve(_leverager, uint256(-1));
    }

    function name() external pure override returns (string memory) {
        return "HomoBasic";
    }

    function estimatedTotalAssets() public view override returns (uint256) {
        return want.balanceOf(address(this)).add(underlyingBalanceStored());
    }

    function underlyingBalanceStored() public view returns (uint256 balance) {
        Bank b = Bank(bank);
        return b.balanceOf(address(this)).mul(_bankTotalEth()).div(b.totalSupply());
    }

    function _bankTotalEth() internal view returns (uint256 _totalEth) {
        Bank b = Bank(bank);

        uint256 interest = b.pendingInterest(0);
        BankConfig config = BankConfig(b.config());
        uint256 toReserve = interest.mul(config.getReservePoolBps()).div(10000);

        uint256 glbDebtVal = b.glbDebtVal().add(interest);
        uint256 reservePool = b.reservePool().add(toReserve);

        _totalEth = bank.balance.add(glbDebtVal).sub(reservePool);
    }

    function apr() external view override returns (uint256) {
        Bank b = Bank(bank);
        BankConfig config = BankConfig(b.config());
        uint256 ratePerSec = config.getInterestRate(b.glbDebtVal(), bank.balance);

        return ratePerSec.mul(secondsPerYear);
    }

    function _liquidatePosition(uint256 _amountNeeded) internal returns (uint256 _amountFreed) {
        uint256 balanceUnderlying = underlyingBalanceStored();
        uint256 looseBalance = want.balanceOf(address(this));
        uint256 total = balanceUnderlying.add(looseBalance);

        if (_amountNeeded > total) {
            //cant withdraw more than we own
            _amountNeeded = total;
        }

        if (looseBalance >= _amountNeeded) {
            return _amountNeeded;
        }

        uint256 liquidity = bank.balance;
        if (liquidity > 1) {
            uint256 toWithdraw = _amountNeeded.sub(looseBalance);

            if (toWithdraw <= liquidity) {
                withdrawUnderlying(toWithdraw);
            } else {
                withdrawUnderlying(liquidity);
            }
        }

        return want.balanceOf(address(this));
    }

    function liquidatePosition(uint256 _amountNeeded) external override only(leverager) returns (uint256 _amountFreed) {
        return _liquidatePosition(_amountNeeded);
    }

    function prepareReturn(uint256 _debtOutstanding, uint256 _totalDebt)
        external
        override
        only(leverager)
        returns (
            uint256 _profit,
            uint256 _loss,
            uint256 _debtPayment
        )
    {
        _debtPayment = _debtOutstanding;
        uint256 looseAssets = IWETH(weth).balanceOf(address(this));
        uint256 total = estimatedTotalAssets();
        uint256 debt = _totalDebt;

        if (_debtOutstanding > 0) {
            uint256 _amountFreed = _liquidatePosition(_debtOutstanding);
            _debtPayment = Math.min(_amountFreed, _debtOutstanding);
        }

        if (total > debt) {
            _profit = total - debt;
            uint256 amountToFree = _profit.add(_debtPayment);
            if (amountToFree > 0 && looseAssets < amountToFree) {
                withdrawUnderlying(amountToFree.sub(looseAssets));
                uint256 newLoose = want.balanceOf(address(this));

                if (newLoose < amountToFree) {
                    if (_profit > newLoose) {
                        _profit = newLoose;
                        _debtPayment = 0;
                    } else {
                        _debtPayment = Math.min(newLoose - _profit, _debtPayment);
                    }
                }
            }
        }
    }

    function adjustPosition(uint256 _debtOutstanding) external override only(leverager) {
        uint256 wethBalance = IWETH(weth).balanceOf(address(this));
        // Nothing to invest if we have debt
        if (_debtOutstanding >= wethBalance) {
            return;
        }

        uint256 toInvest = wethBalance.sub(_debtOutstanding);
        IWETH(weth).withdraw(toInvest);
        Bank(bank).deposit{value: toInvest}();
    }

    function withdrawUnderlying(uint256 amount) internal returns (uint256) {
        Bank b = Bank(bank);

        uint256 shares = amount.mul(b.totalSupply()).div(_bankTotalEth());
        uint256 balance = b.balanceOf(address(this));
        if (shares > balance) {
            b.withdraw(balance);
        } else {
            b.withdraw(shares);
        }

        uint256 withdrawn = address(this).balance;
        IWETH(weth).deposit{value: withdrawn}();

        return withdrawn;
    }

    function prepareMigration(address _newStrategy) external override only(leverager) {
        Bank(bank).transfer(_newStrategy, Bank(bank).balanceOf(address(this)));
        want.safeTransfer(_newStrategy, want.balanceOf(address(this)));
    }

    function protectedTokens() external view override returns (address[] memory) {
        address[] memory protected = new address[](1);
        protected[0] = address(want);
        return protected;
    }

    receive() external payable {}
}

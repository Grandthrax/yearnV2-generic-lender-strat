// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.6.12;
pragma experimental ABIEncoderV2;

import "@yearnvaults/contracts/BaseStrategy.sol";

import "@openzeppelinV3/contracts/token/ERC20/IERC20.sol";
import "@openzeppelinV3/contracts/math/SafeMath.sol";
import "@openzeppelinV3/contracts/math/Math.sol";
import "@openzeppelinV3/contracts/utils/Address.sol";
import "@openzeppelinV3/contracts/token/ERC20/SafeERC20.sol";

import "../Interfaces/Compound/ComptrollerI.sol";
import "../Interfaces/Compound/CErc20I.sol";
import "./LeveragedStrategy.sol";

contract LeveragedEthStrategy is BaseStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    ComptrollerI public constant ironBank = ComptrollerI(0xAB1c342C7bf5Ec5F02ADEA1c2270670bCa144CbB);
    CErc20I public constant ironBankToken = CErc20I(0x41c84c0e2EE0b740Cf0d31F63f3B6F627DC6b393);
    LeveragedStrategy public inner;
    uint256 public maxIronBankLeverage = 4; //max leverage we will take from iron bank

    constructor(address _vault) public BaseStrategy(_vault) {
        debtThreshold = 1000;
    }

    function setInnerStrategy(address _inner) external onlyAuthorized {
        inner = LeveragedStrategy(_inner);
    }

    // This should be abstract
    function name() external pure override returns (string memory) {
        return "LeveragedEth";
    }

    function estimatedTotalAssets() public view override returns (uint256) {
        return inner.estimatedTotalAssets().sub(ironBankOutstandingDebtStored());
    }

    function prepareReturn(uint256 _debtOutstanding)
        internal
        override
        returns (
            uint256 _profit,
            uint256 _loss,
            uint256 _debtPayment
        )
    {
        uint256 stratDebt = vault.strategies(address(this)).totalDebt;
        uint256 _totalDebt = stratDebt.add(ironBankOutstandingDebtStored());
        (_profit, _loss, _debtPayment) = inner.prepareReturn(_debtOutstanding, _totalDebt);
        want.transferFrom(address(inner), address(this), want.balanceOf(address(inner)));
    }

    event AdjustPosition(bool borrowMore, uint256 amount);

    function adjustPosition(uint256 _debtOutstanding) internal override {
        //emergency exit is dealt with at beginning of harvest
        if (emergencyExit) {
            return;
        }

        //start off by borrowing or returning:
        (bool borrowMore, uint256 amount) = internalCreditOfficer();
        emit AdjustPosition(borrowMore, amount);
        //if repaying we use debOutstanding
        if (!borrowMore) {
            _debtOutstanding = amount;
        } else if (amount > 0) {
            ironBankToken.borrow(amount);
            want.transfer(address(inner), want.balanceOf(address(this)));
        }

        inner.adjustPosition(_debtOutstanding);
    }

    function ironBankBorrowRate(uint256 amount, bool repay) public view returns (uint256) {
        uint256 cashPrior = want.balanceOf(address(ironBankToken));
        uint256 borrows = ironBankToken.totalBorrows();
        uint256 reserves = ironBankToken.totalReserves();

        InterestRateModel model = ironBankToken.interestRateModel();
        uint256 cashChange;
        uint256 borrowChange;
        if (repay) {
            cashChange = cashPrior.add(amount);
            borrowChange = borrows.sub(amount);
        } else {
            cashChange = cashPrior.sub(amount);
            borrowChange = borrows.add(amount);
        }

        return model.getBorrowRate(cashChange, borrowChange, reserves);
    }

    function ironBankOutstandingDebtStored() public view returns (uint256) {
        return ironBankToken.borrowBalanceStored(address(this));
    }

    function ironBankRemainingCredit() public view returns (uint256 available) {
        (, uint256 liquidity, ) = ironBank.getAccountLiquidity(address(this));
        if (liquidity == 0) {
            return 0;
        }

        uint256 underlyingPrice = ironBank.oracle().getUnderlyingPrice(address(ironBankToken));

        if (underlyingPrice == 0) {
            return 0;
        }
        uint256 liquidityAvailable = want.balanceOf(address(ironBankToken));

        available = liquidity.mul(1e18).div(underlyingPrice);
        available = Math.min(available, liquidityAvailable);
    }

    function internalCreditOfficer() public view returns (bool borrowMore, uint256 amount) {
        uint256 currentSR = inner.apr();
        uint256 ironBankBR = ironBankBorrowRate(0, true);

        uint256 outstandingDebt = ironBankOutstandingDebtStored();
        uint256 remainingCredit = ironBankRemainingCredit();
        //we have internal credit limit. it is function on our own assets invested
        //this means we can always repay our debt from our capital
        uint256 maxCreditDesired = vault.strategies(address(this)).totalDebt.mul(maxIronBankLeverage);
        remainingCredit = Math.min(maxCreditDesired, remainingCredit);

        //minIncrement must be > 0
        if (remainingCredit < 11) {
            return (false, 0);
        }

        //we move in 10% increments
        uint256 minIncrement = maxCreditDesired.div(10);

        //we start at 1 to save some gas
        uint256 increment = 1;

        //if sr is > iron bank we borrow more. else return
        if (currentSR > ironBankBR) {
            while (minIncrement.mul(increment) <= remainingCredit) {
                ironBankBR = ironBankBorrowRate(minIncrement.mul(increment), false);
                if (currentSR <= ironBankBR) {
                    break;
                }

                increment++;
            }

            borrowMore = true;
            amount = minIncrement.mul(increment - 1);
        } else {
            while (minIncrement.mul(increment) <= outstandingDebt) {
                ironBankBR = ironBankBorrowRate(minIncrement.mul(increment), false);

                //we do increment before the if statement here
                increment++;
                if (currentSR > ironBankBR) {
                    break;
                }
            }
            borrowMore = false;

            //special case to repay all
            if (increment == 1) {
                amount = outstandingDebt;
            } else {
                amount = minIncrement.mul(increment - 1);
            }
        }
    }

    function exitPosition(uint256 _debtOutstanding)
        internal
        override
        returns (
            uint256 _profit,
            uint256 _loss,
            uint256 _debtPayment
        )
    {
        return prepareReturn(_debtOutstanding);
    }

    function liquidatePosition(uint256 _amountNeeded) internal override returns (uint256 _amountFreed) {
        _amountFreed = inner.liquidatePosition(_amountNeeded);
        want.transferFrom(address(inner), address(this), _amountFreed);
    }

    function prepareMigration(address _newStrategy) internal override {
        require(false, "cant migrate");
    }

    function protectedTokens() internal view override returns (address[] memory) {
        address[] memory protected = new address[](2);
        protected[0] = address(want);
        protected[1] = address(0x41c84c0e2EE0b740Cf0d31F63f3B6F627DC6b393); // cyweth
        return protected;
    }
}

// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import "@yearnvaults/contracts/BaseStrategy.sol";

import "@openzeppelinV3/contracts/token/ERC20/IERC20.sol";
import "@openzeppelinV3/contracts/math/SafeMath.sol";
import "@openzeppelinV3/contracts/math/Math.sol";
import "@openzeppelinV3/contracts/utils/Address.sol";
import "@openzeppelinV3/contracts/token/ERC20/SafeERC20.sol";

import "../Interfaces/Compound/ComptrollerI.sol";
import "../Interfaces/Compound/CErc20I.sol";
import "./ILeveragedStrategy.sol";

contract LeveragedEthStrategy is BaseStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    ComptrollerI public constant ironBank = ComptrollerI(0xAB1c342C7bf5Ec5F02ADEA1c2270670bCa144CbB);
    CErc20I public constant ironBankToken = CErc20I(0x41c84c0e2EE0b740Cf0d31F63f3B6F627DC6b393);
    ILeveragedStrategy public inner;

    uint256 public step = 10;
    uint256 public maxIronBankLeverage = 4; //max leverage we will take from iron bank

    constructor(address _vault) public BaseStrategy(_vault) {
        debtThreshold = 1000;
    }

    function setInnerStrategy(address _inner) external onlyAuthorized {
        inner = ILeveragedStrategy(_inner);
    }

    function name() external pure override returns (string memory) {
        //return string(abi.encodePacked("LeveragedEth", inner.name()));
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
        uint256 totalDebt = stratDebt.add(ironBankOutstandingDebtStored());

        // prepareReturn is done in the inner strat but we need to send _totalDebt
        // since the entity with the debt with the vault is this class
        (_profit, _loss, _debtPayment) = inner.prepareReturn(_debtOutstanding, totalDebt);

        // We need to transfer want from inner to this so BaseStrategy can do the harvest work
        want.transferFrom(address(inner), address(this), want.balanceOf(address(inner)));
    }

    function adjustPosition(uint256 _debtOutstanding) internal override {
        //emergency exit is dealt with at beginning of harvest
        if (emergencyExit) {
            return;
        }

        //start off by borrowing or returning:
        (bool borrowMore, uint256 amount) = internalCreditOfficer();

        //if repaying we use debOutstanding
        if (!borrowMore) {
            _debtOutstanding = amount;
        } else if (amount > 0) {
            ironBankToken.borrow(amount);
        }

        //we are spending all our cash unless we have debt outstanding
        uint256 _wantBal = want.balanceOf(address(this));

        if(_wantBal < _debtOutstanding) {
            //this is graceful withdrawal. dont use backup
            //we use more than 1 because withdraw underlying causes problems with 1 token due to different decimals
            //if(ironBankToken.balanceOf(address(this)) > 1) {
                //_withdrawSome(_debtOutstanding - _wantBal);
            //}

            if(!borrowMore) {
                ironBankToken.repayBorrow(Math.min(_debtOutstanding, want.balanceOf(address(this))));
            }
            return;
        }

        // If we get to this point, we should invest want
        // send to inner and adjustPosition
        want.transfer(address(inner), want.balanceOf(address(this)));
        inner.adjustPosition(_debtOutstanding);
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
        address[] memory protected = new address[](1);
        protected[0] = address(0x41c84c0e2EE0b740Cf0d31F63f3B6F627DC6b393); // cyweth
        return protected;
    }

    function tendTrigger(uint256 gasCost) public override view returns (bool) {
        if (harvestTrigger(gasCost)) {
            //harvest takes priority
            return false;
        }

        //test if we want to change iron bank position
        (,uint256 _amount) = internalCreditOfficer();
        if(profitFactor.mul(gasCost) < _amount) {
            return true;
        }
    }

    function ironBankBorrowRate(uint256 amount, bool repay) public view returns (uint256) {
       uint256 cashPrior = want.balanceOf(address(ironBankToken));

       uint256 borrows = ironBankToken.totalBorrows();
       uint256 reserves = ironBankToken.totalReserves();

       InterestRateModel model = ironBankToken.interestRateModel();
       uint256 cashChange;
       uint256 borrowChange;
       if(repay){
           cashChange = cashPrior.add(amount);
           borrowChange = borrows.sub(amount);
       }else{
           cashChange = cashPrior.sub(amount);
           borrowChange = borrows.add(amount);
       }

       uint256 borrowRate = model.getBorrowRate(cashChange, borrowChange, reserves);

       return borrowRate;
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

    function currentSupplyRate() public view returns (uint256 supply) {
        return inner.apr();
    }

    //simple logic. do we get more apr than iron bank charges?
    //if so, is that still true with increased pos?
    //if not, should be reduce?
    //made harder because we can't assume iron bank debt curve. So need to increment
    function internalCreditOfficer() public view returns (bool borrowMore, uint256 amount) {

        //how much credit we have
        (, uint256 liquidity, uint256 shortfall) = ironBank.getAccountLiquidity(address(this));
        uint256 underlyingPrice = ironBank.oracle().getUnderlyingPrice(address(ironBankToken));

        if(underlyingPrice == 0){
            return (false, 0);
        }

        liquidity = liquidity.mul(1e18).div(underlyingPrice);
        shortfall = shortfall.mul(1e18).div(underlyingPrice);

        //repay debt if iron bank wants its money back
        if(shortfall > 0){
            //note we only borrow 1 asset so can assume all our shortfall is from it
            return(false, shortfall-1); //remove 1 incase of rounding errors
        }


        uint256 liquidityAvailable = want.balanceOf(address(ironBankToken));
        uint256 remainingCredit = Math.min(liquidity, liquidityAvailable);


        //our current supply rate.
        //we only calculate once because it is expensive
        uint256 currentSR = currentSupplyRate();
        //iron bank borrow rate
        uint256 ironBankBR = ironBankBorrowRate(0, true);

        uint256 outstandingDebt = ironBankOutstandingDebtStored();

        //we have internal credit limit. it is function on our own assets invested
        //this means we can always repay our debt from our capital
        uint256 maxCreditDesired = vault.strategies(address(this)).totalDebt.mul(maxIronBankLeverage);


        //minIncrement must be > 0
        if(maxCreditDesired <= step){
            return (false, 0);
        }

        //we move in 10% increments
        uint256 minIncrement = maxCreditDesired.div(step);

        //we start at 1 to save some gas
        uint256 increment = 1;

        // if we have too much debt we return
        if(maxCreditDesired < outstandingDebt){
            borrowMore = false;
            amount = outstandingDebt - maxCreditDesired;
        }
        //if sr is > iron bank we borrow more. else return
        else if(currentSR > ironBankBR){
            remainingCredit = Math.min(maxCreditDesired - outstandingDebt, remainingCredit);

            while(minIncrement.mul(increment) <= remainingCredit){
                ironBankBR = ironBankBorrowRate(minIncrement.mul(increment), false);
                if(currentSR <= ironBankBR){
                    break;
                }

                increment++;
            }
            borrowMore = true;
            amount = minIncrement.mul(increment-1);

        } else {

            while(minIncrement.mul(increment) <= outstandingDebt) {
                ironBankBR = ironBankBorrowRate(minIncrement.mul(increment), true);

                //we do increment before the if statement here
                increment++;
                if(currentSR > ironBankBR){
                    break;
                }

            }
            borrowMore = false;

            //special case to repay all
            if(increment == 1) {
                amount = outstandingDebt;
            } else {
                amount = minIncrement.mul(increment - 1);
            }

        }

        //we dont play with dust:
        if (amount < debtThreshold) {
            amount = 0;
        }
     }
}

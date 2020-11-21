pragma solidity ^0.6.12;
pragma experimental ABIEncoderV2;

import "@openzeppelinV3/contracts/token/ERC20/IERC20.sol";
import "@openzeppelinV3/contracts/math/SafeMath.sol";
import "@openzeppelinV3/contracts/utils/Address.sol";
import "@openzeppelinV3/contracts/token/ERC20/SafeERC20.sol";

import "../Interfaces/alpha-homora/Bank.sol";
import "../Interfaces/alpha-homora/BankConfig.sol";
import "../Interfaces/UniswapInterfaces/IWETH.sol";

import "./IGenericLender.sol";

/********************
 *   A lender plugin for LenderYieldOptimiser for any erc20 asset on Cream (not eth)
 *   Made by SamPriestley.com
 *   https://github.com/Grandthrax/yearnv2/blob/master/contracts/GenericLender/GenericCream.sol
 *
 ********************* */

contract AlphaHomo is IGenericLender {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    uint256 private constant secondsPerYear = 31556952;
    address public constant weth = address(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2);
    address public constant bank = address(0x67B66C99D3Eb37Fa76Aa3Ed1ff33E8e39F0b9c7A);

    constructor(address _strategy, string memory name) public IGenericLender(_strategy, name) {
        require(address(want) == weth, "NOT WETH");

        //want.approve(_cToken, uint256(-1));
    }

    receive() external payable {}

    function nav() external view override returns (uint256) {
        return _nav();
    }

    function _nav() internal view returns (uint256) {
        return want.balanceOf(address(this)).add(underlyingBalanceStored());
    }

    function bankBalance() internal view returns (uint256 _profit) {
        Bank b = Bank(bank);
        return b.balanceOf(address(this)).mul(b.totalETH().add(b.pendingInterest(0))).div(b.totalSupply());
        //return b.debtShareToVal( b.balanceOf(address(this)));
    }

    function withdrawUnderlying(uint256 amount) internal returns (uint256) {
        Bank b = Bank(bank);

        uint256 shares = amount.mul(b.totalSupply()).div(b.totalETH());
        // uint256 shares = b.debtValToShare(amount);
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

    function underlyingBalanceStored() public view returns (uint256 balance) {
        Bank b = Bank(bank);
        return b.balanceOf(address(this)).mul(b.totalETH().add(b.pendingInterest(0))).div(b.totalSupply());
    }

    function apr() external view override returns (uint256) {
        return _apr(0);
    }

    function aprAfterDeposit(uint256 amount) external view override returns (uint256) {
        return _apr(amount);
    }

    function _apr(uint256 amount) internal view returns (uint256) {
        Bank b = Bank(bank);
        BankConfig config = BankConfig(b.config());
        uint256 balance = bank.balance.add(amount);
        uint256 ratePerSec = config.getInterestRate(b.glbDebtVal(), balance);

        return ratePerSec.mul(secondsPerYear);
    }

    function weightedApr() external view override returns (uint256) {
        uint256 a = _apr(0);
        return a.mul(_nav());
    }

    function withdraw(uint256 amount) external override management returns (uint256) {
        return _withdraw(amount);
    }

    //emergency withdraw. sends balance plus amount to governance
    function emergencyWithdraw(uint256 amount) external override management {
        withdrawUnderlying(amount);

        want.safeTransfer(vault.governance(), want.balanceOf(address(this)));
    }

    //withdraw an amount including any want balance
    function _withdraw(uint256 amount) internal returns (uint256) {
        uint256 balanceUnderlying = underlyingBalanceStored();
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
        uint256 liquidity = bank.balance;

        if (liquidity > 1) {
            uint256 toWithdraw = amount.sub(looseBalance);

            if (toWithdraw <= liquidity) {
                //we can take all
                withdrawUnderlying(toWithdraw);
            } else {
                //take all we can
                withdrawUnderlying(liquidity);
            }
        }
        looseBalance = want.balanceOf(address(this));
        want.safeTransfer(address(strategy), looseBalance);
        return looseBalance;
    }

    function deposit() external override management {
        uint256 balance = want.balanceOf(address(this));

        IWETH(weth).withdraw(balance);
        Bank(bank).deposit{value: balance}();
    }

    function withdrawAll() external override management returns (bool) {
        uint256 invested = _nav();
        uint256 returned = _withdraw(invested);
        return returned >= invested;
    }

    //think about this
    function enabled() external view override returns (bool) {
        return true;
    }

    function hasAssets() external view override returns (bool) {
        return Bank(bank).balanceOf(address(this)) > 0;
    }

    function protectedTokens() internal view override returns (address[] memory) {
        address[] memory protected = new address[](2);
        protected[0] = address(want);
        protected[1] = bank;
        return protected;
    }
}

// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

import "../Interfaces/UniswapInterfaces/IUniswapV2Router02.sol";

import "./GenericLenderBase.sol";
import "../Interfaces/Aave/IAToken.sol";
import "../Interfaces/Aave/IStakedAave.sol";
import "../Interfaces/Aave/ILendingPool.sol";
import "../Interfaces/Aave/IProtocolDataProvider.sol";
import "../Interfaces/Aave/IAaveIncentivesController.sol";
import "../Interfaces/Aave/IReserveInterestRateStrategy.sol";
import "../Libraries/Aave/DataTypes.sol";

/********************
 *   A lender plugin for LenderYieldOptimiser for any erc20 asset on Aave
 *   Made by SamPriestley.com & jmonteer
 *   https://github.com/Grandthrax/yearnv2/blob/master/contracts/GenericLender/GenericAave.sol
 *
 ********************* */

contract GenericAave is GenericLenderBase {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    IProtocolDataProvider public constant protocolDataProvider = IProtocolDataProvider(address(0x057835Ad21a177dbdd3090bB1CAE03EaCF78Fc6d));
    IAToken public aToken;
    IStakedAave public constant stkAave = IStakedAave(0x4da27a545c0c5B758a6BA100e3a049001de870f5);

    bool public isIncentivised;
    uint16 internal constant DEFAULT_REFERRAL = 179; // jmonteer's referral code
    uint16 internal customReferral;

    address public constant WETH =
        address(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2);

    address public constant AAVE =
        address(0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9);

    IUniswapV2Router02 public constant router =
        IUniswapV2Router02(address(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D));

    uint256 constant internal SECONDS_IN_YEAR = 365 days;

    constructor(
        address _strategy,
        string memory name,
        IAToken _aToken,
        bool _isIncentivised
    ) public GenericLenderBase(_strategy, name) {
        _initialize(_aToken, _isIncentivised);
    }

    function initialize(IAToken _aToken, bool _isIncentivised) external {
        _initialize(_aToken, _isIncentivised);
    }

    function cloneAaveLender(
        address _strategy,
        string memory _name,
        IAToken _aToken,
        bool _isIncentivised
    ) external returns (address newLender) {
        newLender = _clone(_strategy, _name);
        GenericAave(newLender).initialize(_aToken, _isIncentivised);
    }

    // for the management to activate / deactivate incentives functionality
    function setIsIncentivised(bool _isIncentivised) external management {
        // NOTE: if the aToken is not incentivised, getIncentivesController() might revert (aToken won't implement it)
        // to avoid calling it, we use the OR and lazy evaluation
        require(!_isIncentivised || address(aToken.getIncentivesController()) != address(0), "!aToken does not have incentives controller set up");
        isIncentivised = _isIncentivised;
    }

    function setReferralCode(uint16 _customReferral) external management {
        require(_customReferral != 0, "!invalid referral code");
        customReferral = _customReferral;
    }

    function withdraw(uint256 amount) external override management returns (uint256) {
        return _withdraw(amount);
    }

    //emergency withdraw. sends balance plus amount to governance
    function emergencyWithdraw(uint256 amount) external override management {
        _lendingPool().withdraw(address(want), amount, address(this));

        want.safeTransfer(vault.governance(), want.balanceOf(address(this)));
    }

    function deposit() external override management {
        uint256 balance = want.balanceOf(address(this));
        _deposit(balance);
    }

    function withdrawAll() external override management returns (bool) {
        uint256 invested = _nav();
        uint256 returned = _withdraw(invested);
        return returned >= invested;
    }

    function startCooldown() external management {
        // for emergency cases
        IStakedAave(stkAave).cooldown(); // it will revert if balance of stkAave == 0
    }

    function nav() external view override returns (uint256) {
        return _nav();
    }

    function underlyingBalanceStored() public view returns (uint256 balance) {
        balance = aToken.balanceOf(address(this));
    }

    function apr() external view override returns (uint256) {
        return _apr();
    }

    function weightedApr() external view override returns (uint256) {
        uint256 a = _apr();
        return a.mul(_nav());
    }

    // calculates APR from Liquidity Mining Program 
    function _incentivesRate(uint256 totalLiquidity) public view returns (uint256) {
        // only returns != 0 if the incentives are in place at the moment. 
        // it will fail if the isIncentivised is set to true but there is no incentives
        if(isIncentivised && block.timestamp < _incentivesController().getDistributionEnd()) {
            uint256 _emissionsPerSecond;
            (, _emissionsPerSecond, ) = _incentivesController().getAssetData(address(aToken));
            if(_emissionsPerSecond > 0) {
                uint256 emissionsInWant = _AAVEtoWant(_emissionsPerSecond); // amount of emissions in want

                uint256 incentivesRate = emissionsInWant.mul(SECONDS_IN_YEAR).mul(1e18).div(totalLiquidity); // APRs are in 1e18 

                return incentivesRate.mul(9_500).div(10_000); // 95% of estimated APR to avoid overestimations
            }
        }
        return 0;
    }

    function aprAfterDeposit(uint256 extraAmount) external view override returns (uint256) {
        // i need to calculate new supplyRate after Deposit (when deposit has not been done yet)
        DataTypes.ReserveData memory reserveData = _lendingPool().getReserveData(address(want));

        (uint256 availableLiquidity, uint256 totalStableDebt, uint256 totalVariableDebt, , , , uint256 averageStableBorrowRate, , , ) =
            protocolDataProvider.getReserveData(address(want));

        uint256 newLiquidity = availableLiquidity.add(extraAmount);

        (, , , , uint256 reserveFactor, , , , , ) = protocolDataProvider.getReserveConfigurationData(address(want));

        (uint256 newLiquidityRate, , ) =
            IReserveInterestRateStrategy(reserveData.interestRateStrategyAddress).calculateInterestRates(
                address(want),
                newLiquidity,
                totalStableDebt,
                totalVariableDebt,
                averageStableBorrowRate,
                reserveFactor
            );

        uint256 incentivesRate = _incentivesRate(newLiquidity.add(totalStableDebt).add(totalVariableDebt)); // total supplied liquidity in Aave v2
        return newLiquidityRate.div(1e9).add(incentivesRate); // divided by 1e9 to go from Ray to Wad
    }

    function hasAssets() external view override returns (bool) {
        return aToken.balanceOf(address(this)) > 0;
    }

    // Only for incentivised aTokens
    // this is a manual trigger to claim rewards once each 10 days
    // only callable if the token is incentivised by Aave Governance (_checkCooldown returns true)
    function harvest() external management{
        require(_checkCooldown(), "!conditions are not met");
        // redeem AAVE from stkAave
        uint256 stkAaveBalance = IERC20(address(stkAave)).balanceOf(address(this));
        if(stkAaveBalance > 0) {
            stkAave.redeem(address(this), stkAaveBalance);
        }

        // sell AAVE for want
        uint256 aaveBalance = IERC20(AAVE).balanceOf(address(this));
        _sellAAVEForWant(aaveBalance);
        
        // deposit want in lending protocol 
        uint256 balance = want.balanceOf(address(this));
        if(balance > 0) {
            _deposit(balance);
        }

        // claim rewards
        address[] memory assets = new address[](1);
        assets[0] = address(aToken);
        uint256 pendingRewards = _incentivesController().getRewardsBalance(assets, address(this));
        if(pendingRewards > 0) {
            _incentivesController().claimRewards(assets, pendingRewards, address(this));
        }

        // request start of cooldown period
        if(IERC20(address(stkAave)).balanceOf(address(this)) > 0) {
            stkAave.cooldown();
        }
    }

    function harvestTrigger() external view returns (bool) {
        return _checkCooldown();
    }

    function _initialize(IAToken _aToken, bool _isIncentivised) internal {
        require(address(aToken) == address(0), "GenericAave already initialized");

        require(!_isIncentivised || address(_aToken.getIncentivesController()) != address(0), "!aToken does not have incentives controller set up");
        isIncentivised = _isIncentivised;
        aToken = _aToken;
        require(_lendingPool().getReserveData(address(want)).aTokenAddress == address(_aToken), "WRONG ATOKEN");
        IERC20(address(want)).safeApprove(address(_lendingPool()), type(uint256).max);
    }

    function _nav() internal view returns (uint256) {
        return want.balanceOf(address(this)).add(underlyingBalanceStored());
    }

    function _apr() internal view returns (uint256) {
        uint256 liquidityRate = uint256(_lendingPool().getReserveData(address(want)).currentLiquidityRate).div(1e9);// dividing by 1e9 to pass from ray to wad 
        DataTypes.ReserveData memory reserveData = _lendingPool().getReserveData(address(want));
        (uint256 availableLiquidity, uint256 totalStableDebt, uint256 totalVariableDebt, , , , , , , ) =
                    protocolDataProvider.getReserveData(address(want));
        uint256 incentivesRate = _incentivesRate(availableLiquidity.add(totalStableDebt).add(totalVariableDebt)); // total supplied liquidity in Aave v2
        return liquidityRate.add(incentivesRate);
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

    function _deposit(uint256 amount) internal {
        ILendingPool lp = _lendingPool();
        // NOTE: check if allowance is enough and acts accordingly
        // allowance might not be enough if 
        //     i) initial allowance has been used (should take years)
        //     ii) lendingPool contract address has changed (Aave updated the contract address)
        if(want.allowance(address(this), address(lp)) < amount){
            IERC20(address(want)).safeApprove(address(lp), 0);
            IERC20(address(want)).safeApprove(address(lp), type(uint256).max);
        }

        uint16 referral;
        uint16 _customReferral = customReferral;
        if(_customReferral != 0) {
            referral = _customReferral;
        } else {
            referral = DEFAULT_REFERRAL;
        }

        lp.deposit(address(want), amount, address(this), referral);
    }

    function _lendingPool() internal view returns (ILendingPool lendingPool) {
        lendingPool = ILendingPool(protocolDataProvider.ADDRESSES_PROVIDER().getLendingPool());
    }

    function _checkCooldown() internal view returns (bool) {
        if(!isIncentivised) {
            return false;
        }

        uint256 cooldownStartTimestamp = IStakedAave(stkAave).stakersCooldowns(address(this));
        uint256 COOLDOWN_SECONDS = IStakedAave(stkAave).COOLDOWN_SECONDS();
        uint256 UNSTAKE_WINDOW = IStakedAave(stkAave).UNSTAKE_WINDOW();
        if(block.timestamp >= cooldownStartTimestamp.add(COOLDOWN_SECONDS)) {
            return block.timestamp.sub(cooldownStartTimestamp.add(COOLDOWN_SECONDS)) <= UNSTAKE_WINDOW || cooldownStartTimestamp == 0;
        } else {
            return false;
        }
    }

    function _AAVEtoWant(uint256 _amount) internal view returns (uint256) {
        if(_amount == 0) {
            return 0;
        }

        address[] memory path;

        if(address(want) == address(WETH)) {
            path = new address[](2);
            path[0] = address(AAVE);
            path[1] = address(want);
        } else {
            path = new address[](3);
            path[0] = address(AAVE);
            path[1] = address(WETH);
            path[2] = address(want);
        }

        uint256[] memory amounts = router.getAmountsOut(_amount, path);
        return amounts[amounts.length - 1];
    }

    function _sellAAVEForWant(uint256 _amount) internal {
        if (_amount == 0) {
            return;
        }

        address[] memory path;

        if(address(want) == address(WETH)) {
            path = new address[](2);
            path[0] = address(AAVE);
            path[1] = address(want);
        } else {
            path = new address[](3);
            path[0] = address(AAVE);
            path[1] = address(WETH);
            path[2] = address(want);
        }

        if(IERC20(AAVE).allowance(address(this), address(router)) < _amount) {
            IERC20(AAVE).safeApprove(address(router), 0);
            IERC20(AAVE).safeApprove(address(router), type(uint256).max);
        }

        router.swapExactTokensForTokens(
            _amount,
            0,
            path,
            address(this),
            now
        );
    }

    function _incentivesController() internal view returns (IAaveIncentivesController) {
        if(isIncentivised) {
            return aToken.getIncentivesController();
        } else {
            return IAaveIncentivesController(0);
        }
    }

    function protectedTokens() internal view override returns (address[] memory) {
        address[] memory protected = new address[](2);
        protected[0] = address(want);
        protected[1] = address(aToken);
        return protected;
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./Campaign.sol";
import "@openzeppelin/contracts/proxy/ERC1967/ERC1967Proxy.sol";

contract DonationFactory {
    address public campaignImpl;
    address public complianceOracle;
    address public proofNFT;
    address[] public campaigns;

    event CampaignCreated(address indexed campaign, address indexed owner);

    constructor(address _complianceOracle, address _proofNFT) {
        // Деплой логики кампании (UUPS)
        Campaign impl = new Campaign();
        campaignImpl = address(impl);
        complianceOracle = _complianceOracle;
        proofNFT = _proofNFT;
    }

    function createCampaign(address owner) external returns (address) {
        ERC1967Proxy proxy = new ERC1967Proxy(
            campaignImpl,
            abi.encodeWithSelector(Campaign.initialize.selector, owner, complianceOracle, proofNFT)
        );
        campaigns.push(address(proxy));
        emit CampaignCreated(address(proxy), owner);
        return address(proxy);
    }

    function getCampaigns() external view returns (address[] memory) {
        return campaigns;
    }
} 
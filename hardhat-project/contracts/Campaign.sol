// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/proxy/utils/UUPSUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import "@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";

contract Campaign is Initializable, UUPSUpgradeable, OwnableUpgradeable {
    event Donated(address indexed donor, uint256 amount, uint256 timestamp);
    event MilestoneWithdrawn(uint256 milestoneId, uint256 amount);
    event Refunded(address indexed donor, uint256 amount);

    address public complianceOracle;
    address public proofNFT;
    address public factory;

    function initialize(address _owner, address _complianceOracle, address _proofNFT) public initializer {
        __Ownable_init(_owner);
        complianceOracle = _complianceOracle;
        proofNFT = _proofNFT;
        factory = msg.sender;
    }

    function donate() external payable {
        // TODO: Compliance check, mint NFT, record donation
        emit Donated(msg.sender, msg.value, block.timestamp);
    }

    function withdrawMilestone(uint256 milestoneId, uint256 amount) external onlyOwner {
        require(address(this).balance >= amount, "Not enough funds on contract");
        (bool sent, ) = owner().call{value: amount}("");
        require(sent, "Failed to send funds to owner");
        emit MilestoneWithdrawn(milestoneId, amount);
    }

    function refund(address donor, uint256 amount) external onlyOwner {
        require(address(this).balance >= amount, "Not enough funds on contract");
        (bool sent, ) = donor.call{value: amount}("");
        require(sent, "Failed to send funds to donor");
        emit Refunded(donor, amount);
    }

    function _authorizeUpgrade(address newImplementation) internal override onlyOwner {}
} 
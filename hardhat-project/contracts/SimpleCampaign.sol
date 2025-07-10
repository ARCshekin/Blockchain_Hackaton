// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SimpleCampaign {
    address public owner;
    string public title;
    string public description;
    
    event Donated(address indexed donor, uint256 amount, uint256 timestamp);
    
    constructor(string memory _title, string memory _description) {
        owner = msg.sender;
        title = _title;
        description = _description;
    }
    
    function donate() external payable {
        emit Donated(msg.sender, msg.value, block.timestamp);
    }
    
    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    function withdraw(uint256 amount) external onlyOwner {
        require(address(this).balance >= amount, "Not enough funds");
        (bool sent, ) = owner.call{value: amount}("");
        require(sent, "Failed to send funds");
    }
} 
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

// Utility-токен платформы (ERC-20)
contract PlatformToken is ERC20, Ownable {
    // Событие для логирования выпуска токенов
    event Minted(address indexed to, uint256 amount);

    constructor(address initialOwner) ERC20("PlatformToken", "PTKN") Ownable(initialOwner) {}

    // Функция выпуска новых токенов (только владелец)
    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
        emit Minted(to, amount);
    }
} 
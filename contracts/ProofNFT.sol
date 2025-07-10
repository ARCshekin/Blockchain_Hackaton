// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

// Контракт для выдачи NFT-квитанций донору
contract ProofNFT is ERC721URIStorage, Ownable {
    uint256 public nextTokenId;

    // Событие для логирования выпуска NFT
    event Minted(address indexed to, uint256 tokenId, string uri);

    constructor(address initialOwner) ERC721("ProofNFT", "PNFT") Ownable(initialOwner) {}

    // Функция выпуска NFT-квитанции
    function mint(address to, string memory uri) external onlyOwner returns (uint256) {
        uint256 tokenId = nextTokenId++;
        _mint(to, tokenId);
        _setTokenURI(tokenId, uri);
        emit Minted(to, tokenId, uri);
        return tokenId;
    }
} 
# README.md
# storage-soundness-commitment

## Overview
This repo demonstrates a simple Web3 “soundness” check inspired by rollup practices (Aztec-style commitments). Given a contract address, storage slot, and an optional block tag/number, the script:
- Reads the storage value via `eth_getStorageAt`
- Builds a commitment `keccak(chainId || address || slot || value || blockNumber)`
- (Optionally) Cross-checks the same query against a second RPC to detect inconsistencies
This mirrors how systems create succinct commitments to state and rely on soundness: if two honest views of the same state disagree, your commitment comparison reveals it immediately.

## Files
- app.py — CLI script to fetch a storage slot and generate a commitment.
- README.md — this document.

## Requirements
- Python 3.10+
- web3.py
- An Ethereum-compatible RPC endpoint

## Install
1) (Optional) Create and activate a virtual environment.
2) Install dependency:
   pip install web3
3) Set RPC endpoints:
   - Primary: either edit RPC_URL in app.py or set an environment variable:
     export RPC_URL="https://mainnet.infura.io/v3/<key>"
   - (Optional) Secondary for cross-checks:
     export RPC_URL_2="https://rpc.ankr.com/eth"  (or any other)

## Usage
Basic form:
   python app.py <contract_address> <slot(hex|int)> [block_tag|block_number]

## Arguments
- contract_address — EVM contract address (checksum or 0x… hex).
- slot — storage slot index; integer (e.g., 5) or hex (e.g., 0x5).
- block_tag|block_number — optional; one of latest|finalized|safe|pending or a specific block number. Defaults to latest.

## Examples
1) Read slot 0 of a contract at latest block:
   python app.py 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 0x0

2) Read slot 5 of the deposit contract at a fixed block:
   python app.py 0x00000000219ab540356cBB839Cbe05303d7705Fa 5 18000000

3) Cross-check soundness using two providers (set RPC_URL_2 first):
   python app.py 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 1 latest

## Expected Output
- The detected network and chain ID
- Address, slot (hex and decimal), and block number used
- Value read from the slot (hex)
- A deterministic commitment hash
- If a second RPC is configured, a cross-check section comparing chain IDs, block numbers, values, and commitments, ending with either “Soundness confirmed” or a warning

## Notes
- Works with Mainnet, Sepolia, L2s (Optimism, Arbitrum, etc.) and sidechains (Polygon) as long as your RPC supports `eth_getStorageAt` at the requested block.
- For historical checks, some providers require archival access; otherwise, you may see errors or mismatched blocks.
- The commitment is a conceptual stand-in (not a ZK proof). To integrate true zero-knowledge, feed the tuple (chainId, address, slot, value, blockNumber) into a circuit (e.g., circom/halo2) and prove membership/consistency without revealing sensitive data.
- This pattern underlies many airdrop snapshots, rollup state roots, and audit trails: small commitments, strong soundness.

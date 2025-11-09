# app.py
import os
import sys
from web3 import Web3
from typing import Optional, Union

# Primary RPC (override with ENV if you prefer)
RPC_URL = os.getenv("RPC_URL", "https://mainnet.infura.io/v3/your_api_key")
# Optional secondary RPC for cross-checking soundness
RPC_URL_2 = os.getenv("RPC_URL_2")  # e.g., another provider or archival node

NETWORKS = {
    1: "Ethereum Mainnet",
    11155111: "Sepolia Testnet",
    10: "Optimism",
    137: "Polygon",
    42161: "Arbitrum One",
}

def network_name(chain_id: int) -> str:
    return NETWORKS.get(chain_id, f"Unknown (chain ID {chain_id})")

def parse_slot(slot_str: str) -> int:
    if slot_str.startswith("0x") or slot_str.startswith("0X"):
        return int(slot_str, 16)
    return int(slot_str)

def parse_block_tag(block_arg: Optional[str]) -> Union[int, str]:
    if block_arg is None:
        return "latest"
    if block_arg.lower() in ("latest", "finalized", "safe", "pending"):
        return block_arg.lower()
    # numeric
    return int(block_arg, 0)

def get_w3(rpc: str) -> Web3:
    w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 30}))
    if not w3.is_connected():
        print(f"❌ Failed to connect: {rpc}")
        sys.exit(1)
    return w3

def fetch_storage_commitment(
    w3: Web3, address: str, slot: int, block_tag: Union[int, str]
):
    checksum = Web3.to_checksum_address(address)
    value = w3.eth.get_storage_at(checksum, slot, block_identifier=block_tag)
    # Resolve block number for the tag
    if isinstance(block_tag, int):
        block_number = block_tag
    else:
        block_number = w3.eth.block_number if block_tag == "latest" else w3.eth.get_block(block_tag).number
    # Build commitment: keccak(chainId || address || slot || value || blockNumber)
    chain_id = w3.eth.chain_id
    payload = (
        chain_id.to_bytes(8, "big")
        + bytes.fromhex(checksum[2:])
        + slot.to_bytes(32, "big")
        + value.rjust(32, b"\x00")
        + block_number.to_bytes(8, "big")
    )
    commitment = Web3.keccak(payload)
    return {
        "chain_id": chain_id,
        "network": network_name(chain_id),
        "address": checksum,
        "slot": slot,
        "block_number": block_number,
        "value_hex": "0x" + value.hex(),
        "commitment": "0x" + commitment.hex(),
    }

def print_result(label: str, res: dict):
    print(f"— {label} —")
    print(f"🌐 Network: {res['network']} (chainId {res['chain_id']})")
    print(f"🏷️  Address: {res['address']}")
    print(f"📦 Slot: {hex(res['slot'])} ({res['slot']})")
    print(f"🔢 Block: {res['block_number']}")
    print(f"🧱 Value@slot: {res['value_hex']}")
    print(f"🧩 Commitment: {res['commitment']}")

def main():
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python app.py <contract_address> <slot(hex|int)> [block_tag|block_number]")
        print("Examples:")
        print("  python app.py 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 0x0")
        print("  python app.py 0x00000000219ab540356cBB839Cbe05303d7705Fa 5 latest")
        print("  python app.py 0xYourContract 0x1 18000000")
        sys.exit(1)

    address = sys.argv[1]
    slot = parse_slot(sys.argv[2])
    block_tag = parse_block_tag(sys.argv[3]) if len(sys.argv) == 4 else "latest"

    # Primary node
    w3 = get_w3(RPC_URL)
    res1 = fetch_storage_commitment(w3, address, slot, block_tag)
    print_result("PRIMARY", res1)

    # Optional cross-check for soundness across two independent providers
    if RPC_URL_2:
        w3b = get_w3(RPC_URL_2)
        res2 = fetch_storage_commitment(w3b, address, slot, block_tag)
        print_result("SECONDARY", res2)

        same_chain = res1["chain_id"] == res2["chain_id"]
        same_block = res1["block_number"] == res2["block_number"]
        same_value = res1["value_hex"] == res2["value_hex"]
        same_commit = res1["commitment"] == res2["commitment"]

        print("— Cross-Check —")
        print(f"Chain IDs match: {'✅' if same_chain else '❌'}")
        print(f"Block numbers match: {'✅' if same_block else '❌'}")
        print(f"Storage values match: {'✅' if same_value else '❌'}")
        print(f"Commitments match: {'✅' if same_commit else '❌'}")

        if all([same_chain, same_block, same_value, same_commit]):
            print("🔒 Soundness confirmed across providers.")
        else:
            print("⚠️  Potential inconsistency detected — recheck RPCs, block tag, or use archival nodes.")

if __name__ == "__main__":
    main()

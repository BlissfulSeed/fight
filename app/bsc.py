import asyncio
import httpx
from app.config import settings

TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


async def verify_transaction(tx_hash: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(settings.bscscan_api_url, params={
            "module": "proxy",
            "action": "eth_getTransactionReceipt",
            "txhash": tx_hash,
            "apikey": settings.bscscan_api_key,
        })

        if resp.status_code != 200:
            return {"valid": False, "amount": 0, "error": "BscScan API unavailable"}

        data = resp.json()
        result = data.get("result")

        if not result:
            return {"valid": False, "amount": 0, "error": "Transaction not found or still pending"}

        if result.get("status") != "0x1":
            return {"valid": False, "amount": 0, "error": "Transaction failed on-chain"}

        contract_addr = (result.get("to") or "").lower()
        if contract_addr != settings.usdt_contract.lower():
            return {"valid": False, "amount": 0, "error": "Not a USDT transaction"}

        our_wallet = "0x" + settings.wallet_address.lower().replace("0x", "").zfill(64)

        for log in result.get("logs", []):
            topics = log.get("topics", [])
            if (
                len(topics) >= 3
                and topics[0] == TRANSFER_TOPIC
                and topics[2].lower() == our_wallet
            ):
                raw_amount = int(log["data"], 16)
                amount = raw_amount / (10 ** 18)

                if amount >= settings.usdt_amount:
                    return {"valid": True, "amount": amount, "error": None}
                else:
                    return {
                        "valid": False,
                        "amount": amount,
                        "error": f"Insufficient: {amount} USDT (need {settings.usdt_amount})",
                    }

        return {"valid": False, "amount": 0, "error": "No USDT transfer to our wallet in this transaction"}


async def verify_with_retry(tx_hash: str, max_retries: int = 3) -> dict:
    result = None
    for attempt in range(max_retries):
        result = await verify_transaction(tx_hash)
        if result["error"] != "BscScan API unavailable":
            return result
        await asyncio.sleep(2 ** attempt)
    return result

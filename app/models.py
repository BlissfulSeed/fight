from pydantic import BaseModel, Field


class VoteRequest(BaseModel):
    character: str = Field(..., pattern="^(left|right)$")
    tx_hash: str = Field(..., min_length=66, max_length=66)


class VoteResponse(BaseModel):
    success: bool
    message: str
    votes: dict


class VoteCounts(BaseModel):
    left: int = 0
    right: int = 0


class ConfigResponse(BaseModel):
    left_name: str
    right_name: str
    wallet_address: str
    usdt_amount: float
    network: str = "BSC (BEP-20)"

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import aiosqlite

from app.config import settings
from app.database import init_db, get_db, get_vote_counts
from app.bsc import verify_with_retry
from app.phantom import phantom_voter
from app.models import VoteRequest, VoteResponse, VoteCounts, ConfigResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    task = asyncio.create_task(phantom_voter())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Vote Battle", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "left_name": settings.left_character_name,
        "right_name": settings.right_character_name,
    })


@app.get("/api/votes")
async def get_votes():
    counts = await get_vote_counts()
    return VoteCounts(left=counts.get("left", 0), right=counts.get("right", 0))


@app.get("/api/config")
async def get_config():
    return ConfigResponse(
        left_name=settings.left_character_name,
        right_name=settings.right_character_name,
        wallet_address=settings.wallet_address,
        usdt_amount=settings.usdt_amount,
    )


@app.post("/api/vote")
async def submit_vote(vote: VoteRequest):
    tx_hash = vote.tx_hash.strip().lower()
    if not tx_hash.startswith("0x") or len(tx_hash) != 66:
        raise HTTPException(400, "Invalid transaction hash format")

    db = await get_db()
    try:
        cursor = await db.execute("SELECT id FROM votes WHERE tx_hash = ?", (tx_hash,))
        if await cursor.fetchone():
            raise HTTPException(409, "This transaction has already been used to vote")

        try:
            await db.execute(
                "INSERT INTO votes (character, tx_hash, amount, verified, is_phantom) "
                "VALUES (?, ?, 0, 0, 0)",
                (vote.character, tx_hash),
            )
            await db.commit()
        except aiosqlite.IntegrityError:
            raise HTTPException(409, "This transaction has already been used to vote")
    finally:
        await db.close()

    result = await verify_with_retry(tx_hash)

    db = await get_db()
    try:
        if result["valid"]:
            await db.execute(
                "UPDATE votes SET verified = 1, amount = ? WHERE tx_hash = ?",
                (result["amount"], tx_hash),
            )
            await db.commit()
            counts = await get_vote_counts()
            return VoteResponse(
                success=True,
                message="Vote recorded! Thank you!",
                votes=counts,
            )
        else:
            await db.execute("DELETE FROM votes WHERE tx_hash = ?", (tx_hash,))
            await db.commit()
            raise HTTPException(400, f"Payment verification failed: {result['error']}")
    finally:
        await db.close()

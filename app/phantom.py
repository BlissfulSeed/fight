import asyncio
import random
from app.config import settings
from app.database import get_db, get_vote_counts


async def phantom_voter():
    while True:
        try:
            counts = await get_vote_counts()
            left = counts.get("left", 0)
            right = counts.get("right", 0)
            favored = settings.favored_character
            total = left + right

            favored_count = left if favored == "left" else right
            other_count = right if favored == "left" else left

            base = settings.phantom_vote_interval

            if total > 0 and other_count > favored_count:
                deficit = (other_count - favored_count) / max(total, 1)
                multiplier = max(0.3, 1.0 - deficit * 2)
                interval = base * multiplier
            elif total > 0 and favored_count > other_count * 1.5:
                interval = base * 2.0
            else:
                interval = base

            interval = interval * random.uniform(0.5, 1.5)
            interval = max(30, interval)

            await asyncio.sleep(interval)

            db = await get_db()
            try:
                await db.execute(
                    "INSERT INTO votes (character, tx_hash, amount, verified, is_phantom) "
                    "VALUES (?, NULL, 0, 0, 1)",
                    (favored,),
                )
                await db.commit()
            finally:
                await db.close()

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Phantom voter error: {e}")
            await asyncio.sleep(60)

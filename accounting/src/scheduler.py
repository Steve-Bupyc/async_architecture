import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from src.db.base import Types, db
from src.db.models import Payment, Transaction, User
from src.schemas import TransactionCreateSchema


async def payout_task():
    db_users = db.query(User).filter(User.balance > 0).all()
    for db_user in db_users:
        db_transaction = await Transaction.create(
            TransactionCreateSchema(
                user_guid=db_user.guid,
                amount=db_user.balance,
                description=f"Выплата за таски за {datetime.today()}",
                type=Types.payment,
            )
        )
        await User.reset_balance(db_user.guid)
        await Payment.create(db_transaction.guid, db_transaction.amount)


async def scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(payout_task, CronTrigger(day_of_week="mon-sun", hour=21))

    scheduler.start()
    logger.info("Scheduler worker started.")
    await asyncio.Future()


logger = logging.getLogger(__name__)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    logger.debug("=== Starting the scheduler ===")
    asyncio.run(scheduler())

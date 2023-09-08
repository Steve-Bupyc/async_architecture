from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Date, cast, func
from src.db.base import Base, Types, db, engine
from src.db.models import Transaction, User
from src.schemas import MyStatisticsResponseSchema, StatisticsTotalResponseSchema
from src.utils import get_allowed_user, get_current_active_user

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/statistics/total/", response_model=StatisticsTotalResponseSchema)
async def get_statistics(current_user: Annotated[User, Depends(get_allowed_user)]):
    credit_transactions_total = (
        db.query(func.sum(Transaction.amount).label("total"))
        .filter(Transaction.type == Types.credit, cast(Transaction.created_at, Date) == str(datetime.today()))
        .one(),
    )
    debit_transactions_total = (
        db.query(func.sum(Transaction.amount).label("total"))
        .filter(Transaction.type == Types.debit, cast(Transaction.created_at, Date) == str(datetime.today()))
        .one(),
    )
    return {"total_earned": (credit_transactions_total[0].total - debit_transactions_total[0].total)}


@app.get("/statistics/me/", response_model=MyStatisticsResponseSchema)
async def my_statistics(current_user: Annotated[User, Depends(get_current_active_user)]):
    db_transactions = (
        db.query(Transaction)
        .filter(Transaction.user_guid == current_user.guid, cast(Transaction.created_at, Date) == str(datetime.today()))
        .all()
    )

    return {"balance": current_user.balance, "transactions": db_transactions}

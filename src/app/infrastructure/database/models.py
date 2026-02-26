from sqlalchemy import String, Integer, BigInteger, ForeignKey, Boolean, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional, List


class Base(DeclarativeBase):
    pass


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    delimiter: Mapped[str] = mapped_column(String(5), nullable=False)
    date_column_index: Mapped[int] = mapped_column(Integer, nullable=False)
    description_column_index: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_column_index: Mapped[int] = mapped_column(Integer, nullable=False)
    date_format: Mapped[str] = mapped_column(String(50), default="dd/MM/yyyy")
    decimal_separator: Mapped[str] = mapped_column(String(5), default=".")
    is_income_positive: Mapped[bool] = mapped_column(Boolean, default=True)
    skip_rows: Mapped[int] = mapped_column(Integer, default=1)

    accounts: Mapped[List["Account"]] = relationship(back_populates="template")


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    initial_balance_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    default_template_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("templates.id", ondelete="SET NULL")
    )

    template: Mapped[Optional["Template"]] = relationship(back_populates="accounts")
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="account")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    date_timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )

    account: Mapped["Account"] = relationship(back_populates="transactions")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color_hex: Mapped[int] = mapped_column(Integer, nullable=False)
    icon_name: Mapped[str] = mapped_column(String(50), default="category")
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1)

    parent_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE")
    )

    subcategories: Mapped[List["Category"]] = relationship(
        back_populates="parent", remote_side=[id]
    )
    parent: Mapped[Optional["Category"]] = relationship(back_populates="subcategories")

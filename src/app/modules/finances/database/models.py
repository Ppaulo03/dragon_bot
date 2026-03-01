from time import time
from typing import Optional, List
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import (
    String,
    Integer,
    BigInteger,
    ForeignKey,
    Boolean,
    Table,
    Column,
)


class Base(DeclarativeBase):
    pass


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    delimiter: Mapped[str] = mapped_column(String(5), nullable=False)
    skip_rows: Mapped[int] = mapped_column(Integer, default=1)

    csv_name_pattern: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    expected_header: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    date_column_index: Mapped[int] = mapped_column(Integer, nullable=False)
    description_column_index: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_column_index: Mapped[int] = mapped_column(Integer, nullable=False)
    counterpart_column_index: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    date_format: Mapped[str] = mapped_column(String(50), default="dd/MM/yyyy")
    decimal_separator: Mapped[str] = mapped_column(String(5), default=".")
    is_income_positive: Mapped[bool] = mapped_column(Boolean, default=True)

    accounts: Mapped[List["Account"]] = relationship(back_populates="template")


user_accounts = Table(
    "user_accounts",
    Base.metadata,
    Column(
        "user_id",
        String(50),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "account_id",
        Integer,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # JID do WhatsApp
    name: Mapped[str] = mapped_column(String(100))

    # Relação N x N com Account
    accounts: Mapped[List["Account"]] = relationship(
        secondary=user_accounts, back_populates="users"
    )


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    initial_balance_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    default_template_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("templates.id", ondelete="SET NULL")
    )
    users: Mapped[List["User"]] = relationship(
        "User", secondary=user_accounts, back_populates="accounts", lazy="selectin"
    )
    template: Mapped[Optional["Template"]] = relationship(back_populates="accounts")
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="account")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    entity: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    date_timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_category_automatic: Mapped[bool] = mapped_column(Boolean, default=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    import_timestamp: Mapped[int] = mapped_column(
        BigInteger, default=lambda: int(time.time()), nullable=False
    )

    importation_id: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
    )

    category: Mapped[Optional["Category"]] = relationship()
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
        back_populates="parent", cascade="all, delete-orphan"
    )

    parent: Mapped[Optional["Category"]] = relationship(
        back_populates="subcategories", remote_side=[id]
    )

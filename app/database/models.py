from sqlalchemy import create_engine, Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/twitter_clone_db")

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    fullName = Column(String, nullable=False)
    password = Column(String, nullable=False)

    followers = relationship("Follow", foreign_keys="[Follow.followingId]", back_populates="following")
    following = relationship("Follow", foreign_keys="[Follow.followerId]", back_populates="follower")
    tweets = relationship("Tweet", back_populates="user")

class Follow(Base):
    __tablename__ = "follows"

    followerId = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    followingId = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    follower = relationship("User", foreign_keys=[followerId], back_populates="following")
    following = relationship("User", foreign_keys=[followingId], back_populates="followers")

class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String, unique=True, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

class Tweet(Base):
    __tablename__ = "tweets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(String, nullable=False)
    isPrivate = Column(Boolean, default=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    userId = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="tweets")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_db_and_tables():
    Base.metadata.create_all(engine)

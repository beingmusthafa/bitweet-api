from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

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
    notifications = relationship("Notification", back_populates="user")
    hosted_rooms = relationship("Room", back_populates="host")
    participations = relationship("Participant", back_populates="user")

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

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=True)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")

class Room(Base):
    __tablename__ = "rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    is_live = Column(Boolean, default=False)
    host_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    host = relationship("User", back_populates="hosted_rooms")
    participants = relationship("Participant", back_populates="room", cascade="all, delete-orphan")

class Participant(Base):
    __tablename__ = "participants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_speaker = Column(Boolean, default=False)
    joined_at = Column(DateTime, default=datetime.utcnow)

    room = relationship("Room", back_populates="participants")
    user = relationship("User", back_populates="participations")

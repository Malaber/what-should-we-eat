"""Persistent, single-use auth state shared by every API worker."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, LargeBinary, String, JSON
from sqlalchemy.orm import relationship
from execution.db.database import Base


class Passkey(Base):
    __tablename__ = "passkeys"
    credential_id = Column(String(1024), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    public_key = Column(LargeBinary, nullable=False)
    sign_count = Column(Integer, nullable=False, default=0)
    user = relationship("User")


class AuthFlow(Base):
    __tablename__ = "auth_flows"
    token_hash = Column(String(64), primary_key=True)
    kind = Column(String(32), nullable=False)
    payload = Column(JSON, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    token_hash = Column(String(64), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

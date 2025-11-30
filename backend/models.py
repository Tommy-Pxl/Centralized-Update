from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True)
    hostname = Column(String, unique=True)
    last_scanned = Column(DateTime)

    software = relationship("Software", back_populates="machine")
    history = relationship("UpdateHistory", back_populates="machine")


class Software(Base):
    __tablename__ = "software"

    id = Column(Integer, primary_key=True)
    machine_id = Column(Integer, ForeignKey("machines.id"))
    package = Column(String)
    installed_version = Column(String)
    new_version = Column(String)
    last_checked = Column(DateTime)

    machine = relationship("Machine", back_populates="software")


class UpdateHistory(Base):
    __tablename__ = "update_history"

    id = Column(Integer, primary_key=True)
    machine_id = Column(Integer, ForeignKey("machines.id"))
    package = Column(String)
    old_version = Column(String)
    new_version = Column(String)
    timestamp = Column(DateTime)
    performed_by = Column(String)
    notes = Column(String)

    machine = relationship("Machine", back_populates="history")

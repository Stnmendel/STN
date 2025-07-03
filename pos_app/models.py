from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Urun(Base):
    """Ürün modelini temsil eder."""

    __tablename__ = 'urun'

    id = Column(Integer, primary_key=True)
    barkod = Column(String, unique=True, nullable=False)
    urun_adi = Column(String, nullable=False)
    fiyat = Column(Float, nullable=False)
    stok_miktari = Column(Integer, default=0)

class Kullanici(Base):
    """Kullanıcı modelini temsil eder."""

    __tablename__ = 'kullanici'

    id = Column(Integer, primary_key=True)
    kullanici_adi = Column(String, unique=True, nullable=False)
    sifre = Column(String, nullable=False)

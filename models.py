from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Kullanici(Base):
    """Kullanici tablosu"""

    __tablename__ = "kullanicilar"

    id = Column(Integer, primary_key=True)
    kullanici_adi = Column(String, unique=True)
    sifre = Column(String)
    rol = Column(String)


class Urun(Base):
    """Urun tablosu"""

    __tablename__ = "urunler"

    id = Column(Integer, primary_key=True)
    barkod = Column(String, unique=True)
    urun_adi = Column(String)
    fiyat = Column(Float)
    stok_miktari = Column(Integer)


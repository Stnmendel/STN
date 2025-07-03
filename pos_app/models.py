from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import declarative_base, relationship

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


class Musteri(Base):
    """Cari hesap müşterisi."""

    __tablename__ = 'musteri'

    id = Column(Integer, primary_key=True)
    ad_soyad = Column(String, nullable=False)
    telefon = Column(String)
    adres = Column(Text)
    bakiye = Column(Float, default=0.0)
    kredi_limiti = Column(Float, default=0.0)

    satislar = relationship('SatisKaydi', back_populates='musteri')


class SatisKaydi(Base):
    """Gerçekleşen satışların kaydı."""

    __tablename__ = 'satiskaydi'

    id = Column(Integer, primary_key=True)
    tarih = Column(DateTime, default=datetime.utcnow)
    odeme_tipi = Column(String, nullable=False)
    toplam_tutar = Column(Float, default=0.0)
    musteri_id = Column(Integer, ForeignKey('musteri.id'))

    musteri = relationship('Musteri', back_populates='satislar')


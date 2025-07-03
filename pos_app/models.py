from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Urun(Base):
    """Ürün modelini temsil eder."""

    __tablename__ = 'urun'

    id = Column(Integer, primary_key=True)
    barkod = Column(String, unique=True, nullable=False)
    urun_adi = Column(String, nullable=False)
    fiyat = Column(Float, nullable=False)
    alis_fiyati = Column(Float, default=0.0)
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


class Gider(Base):
    """Kasa çıkışlarını temsil eden giderler."""

    __tablename__ = 'gider'

    id = Column(Integer, primary_key=True)
    aciklama = Column(String, nullable=False)
    tutar = Column(Float, nullable=False)
    tarih = Column(DateTime, default=datetime.utcnow)


class CariHareket(Base):
    """Müşteri hesap hareketleri (tahsilat/tediye)."""

    __tablename__ = 'carihareket'

    id = Column(Integer, primary_key=True)
    musteri_id = Column(Integer, ForeignKey('musteri.id'))
    tutar = Column(Float, nullable=False)
    aciklama = Column(String, nullable=False)
    tarih = Column(DateTime, default=datetime.utcnow)

    musteri = relationship('Musteri')


class Toptanci(Base):
    """Ürünlerin alındığı tedarikçiler."""

    __tablename__ = 'toptanci'

    id = Column(Integer, primary_key=True)
    firma_adi = Column(String, nullable=False)
    telefon = Column(String)
    bakiye = Column(Float, default=0.0)

    alimlar = relationship('MalAlimi', back_populates='toptanci')


class MalAlimi(Base):
    """Alış faturası başlığı."""

    __tablename__ = 'malalimi'

    id = Column(Integer, primary_key=True)
    toptanci_id = Column(Integer, ForeignKey('toptanci.id'))
    fatura_no = Column(String)
    alim_tarihi = Column(DateTime, default=datetime.utcnow)
    toplam_tutar = Column(Float, default=0.0)

    toptanci = relationship('Toptanci', back_populates='alimlar')
    kalemler = relationship('MalAlimiDetay', back_populates='mal_alimi')


class MalAlimiDetay(Base):
    """Alış faturası kalemleri."""

    __tablename__ = 'malalimidetay'

    id = Column(Integer, primary_key=True)
    mal_alimi_id = Column(Integer, ForeignKey('malalimi.id'))
    urun_id = Column(Integer, ForeignKey('urun.id'))
    adet = Column(Integer, default=0)
    birim_alis_fiyati = Column(Float, default=0.0)

    mal_alimi = relationship('MalAlimi', back_populates='kalemler')
    urun = relationship('Urun')


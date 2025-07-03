import sys
import hashlib

from PyQt6 import QtCore, QtGui, QtWidgets
from pathlib import Path
import random
try:
    from barcode import EAN13
    from barcode.writer import ImageWriter
except Exception:
    EAN13 = None
    ImageWriter = None
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import shutil

from .models import (
    Base,
    Kullanici,
    Urun,
    Musteri,
    SatisKaydi,
    SatisKalem,
    Gider,
    CariHareket,
    Ayar,
    Toptanci,
    MalAlimi,
    MalAlimiDetay,
)

DB_URL = "sqlite:///pos.db"

engine = create_engine(DB_URL, echo=False)
Session = sessionmaker(bind=engine)

# Veritabanını oluştur
Base.metadata.create_all(engine)

# Varsayılan admin kullanıcısını ekle
session = Session()
if not session.query(Kullanici).filter_by(kullanici_adi="Admin").first():
    hashed = hashlib.sha256("1".encode()).hexdigest()
    admin = Kullanici(kullanici_adi="Admin", sifre=hashed, rol="Admin")
    session.add(admin)
    session.commit()

for key in ["firma_adi", "adres", "telefon", "fis_alt_mesaj"]:
    if not session.query(Ayar).filter_by(ayar_adi=key).first():
        session.add(Ayar(ayar_adi=key, ayar_degeri=""))

session.commit()
session.close()


def hash_password(password: str) -> str:
    """Şifreyi SHA256 ile hashle."""
    return hashlib.sha256(password.encode()).hexdigest()


class LoginWindow(QtWidgets.QDialog):
    """Kullanıcı giriş ekranı."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Giriş")
        layout = QtWidgets.QFormLayout(self)
        self.username_edit = QtWidgets.QLineEdit()
        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        layout.addRow("Kullanıcı Adı", self.username_edit)
        layout.addRow("Şifre", self.password_edit)
        self.button = QtWidgets.QPushButton("Giriş")
        layout.addWidget(self.button)
        self.button.clicked.connect(self.try_login)
        self.result = None

    def try_login(self):
        session = Session()
        user = (
            session.query(Kullanici)
            .filter_by(kullanici_adi=self.username_edit.text())
            .first()
        )
        if user and user.sifre == hash_password(self.password_edit.text()):
            self.result = user
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(self, "Hata", "Giriş başarısız")
        session.close()


class SaleTable(QtWidgets.QTableWidget):
    """Satış için ürünlerin listelendiği tablo."""

    def __init__(self):
        super().__init__(0, 4)
        self.setHorizontalHeaderLabels(["Ürün Adı", "Adet", "Fiyat", "Toplam"])
        header = self.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)


class ProductManagementWindow(QtWidgets.QWidget):
    """Ürünlerin listelendiği ve düzenlendiği pencere."""

    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Ürün İşlemleri")
        self.setup_ui()
        self.load_products()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.table = QtWidgets.QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "Barkod",
            "Ürün Adı",
            "Satış Fiyatı",
            "Alış Fiyatı",
            "Stok",
        ])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        form = QtWidgets.QFormLayout()
        self.barcode_edit = QtWidgets.QLineEdit()
        self.name_edit = QtWidgets.QLineEdit()
        self.price_edit = QtWidgets.QDoubleSpinBox()
        self.price_edit.setMaximum(999999)
        self.buy_price_edit = QtWidgets.QDoubleSpinBox()
        self.buy_price_edit.setMaximum(999999)
        self.stock_edit = QtWidgets.QSpinBox()
        self.stock_edit.setMaximum(999999)
        form.addRow("Barkod", self.barcode_edit)
        form.addRow("Ürün Adı", self.name_edit)
        form.addRow("Satış Fiyatı", self.price_edit)
        form.addRow("Alış Fiyatı", self.buy_price_edit)
        form.addRow("Stok", self.stock_edit)
        layout.addLayout(form)

        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_save = QtWidgets.QPushButton("Kaydet")
        self.btn_delete = QtWidgets.QPushButton("Sil")
        self.btn_print = QtWidgets.QPushButton("Barkod Yazdır")
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_print)
        layout.addLayout(btn_layout)

        self.btn_save.clicked.connect(self.save_product)
        self.btn_delete.clicked.connect(self.delete_product)
        self.btn_print.clicked.connect(self.print_barcode)
        self.table.itemSelectionChanged.connect(self.fill_form)

    def load_products(self):
        self.table.setRowCount(0)
        for product in self.session.query(Urun).all():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(product.barkod))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(product.urun_adi))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(f"{product.fiyat:.2f}"))
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{product.alis_fiyati:.2f}"))
            self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(str(product.stok_miktari)))

    def fill_form(self):
        items = self.table.selectedItems()
        if not items:
            self.barcode_edit.clear()
            self.name_edit.clear()
            self.price_edit.setValue(0)
            self.buy_price_edit.setValue(0)
            self.stock_edit.setValue(0)
            return
        self.barcode_edit.setText(items[0].text())
        self.name_edit.setText(items[1].text())
        self.price_edit.setValue(float(items[2].text()))
        self.buy_price_edit.setValue(float(items[3].text()))
        self.stock_edit.setValue(int(items[4].text()))

    def generate_barcode(self) -> str:
        base = ''.join(str(random.randint(0, 9)) for _ in range(12))
        digits = [int(x) for x in base]
        odd = sum(digits[::2])
        even = sum(digits[1::2])
        check = (10 - ((odd + even * 3) % 10)) % 10
        return base + str(check)

    def save_product(self):
        code = self.barcode_edit.text().strip()
        if not code:
            code = self.generate_barcode()
            self.barcode_edit.setText(code)

        product = self.session.query(Urun).filter_by(barkod=code).first()
        if not product:
            product = Urun(barkod=code)
            self.session.add(product)

        product.urun_adi = self.name_edit.text()
        product.fiyat = float(self.price_edit.value())
        product.alis_fiyati = float(self.buy_price_edit.value())
        product.stok_miktari = int(self.stock_edit.value())
        self.session.commit()
        self.load_products()

    def delete_product(self):
        code = self.barcode_edit.text().strip()
        product = self.session.query(Urun).filter_by(barkod=code).first()
        if product:
            self.session.delete(product)
            self.session.commit()
            self.load_products()

    def print_barcode(self):
        if EAN13 is None:
            QtWidgets.QMessageBox.warning(self, "Hata", "python-barcode kurulu değil")
            return
        code = self.barcode_edit.text().strip()
        if not code:
            QtWidgets.QMessageBox.warning(self, "Hata", "Barkod seçili değil")
            return
        output_dir = Path('static/barcodes')
        output_dir.mkdir(parents=True, exist_ok=True)
        ean = EAN13(code, writer=ImageWriter())
        ean.save(str(output_dir / code))


class CustomerManagementWindow(QtWidgets.QWidget):
    """Müşterilerin listelendiği ve düzenlendiği pencere."""

    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Müşteri İşlemleri")
        self.setup_ui()
        self.load_customers()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Ad Soyad", "Bakiye", "Telefon"])
        self.table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.table)

        form = QtWidgets.QFormLayout()
        self.name_edit = QtWidgets.QLineEdit()
        self.phone_edit = QtWidgets.QLineEdit()
        self.address_edit = QtWidgets.QTextEdit()
        self.limit_edit = QtWidgets.QDoubleSpinBox()
        self.limit_edit.setMaximum(999999)
        form.addRow("Ad Soyad", self.name_edit)
        form.addRow("Telefon", self.phone_edit)
        form.addRow("Adres", self.address_edit)
        form.addRow("Kredi Limiti", self.limit_edit)
        layout.addLayout(form)

        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_save = QtWidgets.QPushButton("Kaydet")
        self.btn_delete = QtWidgets.QPushButton("Sil")
        self.btn_statement = QtWidgets.QPushButton("Hesap Ekstresi")
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_statement)
        layout.addLayout(btn_layout)

        self.btn_save.clicked.connect(self.save_customer)
        self.btn_delete.clicked.connect(self.delete_customer)
        self.btn_statement.clicked.connect(self.show_statement)
        self.table.itemSelectionChanged.connect(self.fill_form)

    def load_customers(self):
        self.table.setRowCount(0)
        for cust in self.session.query(Musteri).all():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(cust.ad_soyad))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(f"{cust.bakiye:.2f}"))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(cust.telefon or ""))

    def fill_form(self):
        items = self.table.selectedItems()
        if not items:
            self.name_edit.clear()
            self.phone_edit.clear()
            self.address_edit.clear()
            self.limit_edit.setValue(0)
            return
        self.name_edit.setText(items[0].text())
        self.phone_edit.setText(items[2].text())
        cust = (
            self.session.query(Musteri)
            .filter_by(ad_soyad=items[0].text(), telefon=items[2].text())
            .first()
        )
        if cust:
            self.address_edit.setText(cust.adres or "")
            self.limit_edit.setValue(cust.kredi_limiti)

    def save_customer(self):
        name = self.name_edit.text().strip()
        if not name:
            return
        cust = self.session.query(Musteri).filter_by(ad_soyad=name).first()
        if not cust:
            cust = Musteri(ad_soyad=name)
            self.session.add(cust)

        cust.telefon = self.phone_edit.text().strip()
        cust.adres = self.address_edit.toPlainText().strip()
        cust.kredi_limiti = float(self.limit_edit.value())
        self.session.commit()
        self.load_customers()

    def delete_customer(self):
        name = self.name_edit.text().strip()
        cust = self.session.query(Musteri).filter_by(ad_soyad=name).first()
        if cust:
            self.session.delete(cust)
            self.session.commit()
            self.load_customers()

    def show_statement(self):
        items = self.table.selectedItems()
        if not items:
            return
        name = items[0].text()
        cust = self.session.query(Musteri).filter_by(ad_soyad=name).first()
        if not cust:
            return
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Hesap Ekstresi")
        layout = QtWidgets.QVBoxLayout(dlg)
        listw = QtWidgets.QListWidget()
        layout.addWidget(listw)
        for sale in (
            self.session.query(SatisKaydi)
            .filter_by(musteri_id=cust.id)
            .order_by(SatisKaydi.tarih)
        ):
            listw.addItem(
                f"{sale.tarih:%Y-%m-%d %H:%M} - {sale.odeme_tipi} - {sale.toplam_tutar:.2f}"
            )
        btn = QtWidgets.QPushButton("Kapat")
        layout.addWidget(btn)
        btn.clicked.connect(dlg.accept)
        dlg.exec()


class SupplierManagementWindow(QtWidgets.QWidget):
    """Toptancıların yönetimi."""

    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Toptancı İşlemleri")
        self.setup_ui()
        self.load_suppliers()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Firma Adı", "Bakiye", "Telefon"])
        self.table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.table)

        form = QtWidgets.QFormLayout()
        self.name_edit = QtWidgets.QLineEdit()
        self.phone_edit = QtWidgets.QLineEdit()
        form.addRow("Firma Adı", self.name_edit)
        form.addRow("Telefon", self.phone_edit)
        layout.addLayout(form)

        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_save = QtWidgets.QPushButton("Kaydet")
        self.btn_delete = QtWidgets.QPushButton("Sil")
        self.btn_purchase = QtWidgets.QPushButton("Yeni Mal Alımı Yap")
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_purchase)
        layout.addLayout(btn_layout)

        self.btn_save.clicked.connect(self.save_supplier)
        self.btn_delete.clicked.connect(self.delete_supplier)
        self.btn_purchase.clicked.connect(self.new_purchase)
        self.table.itemSelectionChanged.connect(self.fill_form)

    def load_suppliers(self):
        self.table.setRowCount(0)
        for sup in self.session.query(Toptanci).all():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(sup.firma_adi))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(f"{sup.bakiye:.2f}"))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(sup.telefon or ""))

    def fill_form(self):
        items = self.table.selectedItems()
        if not items:
            self.name_edit.clear()
            self.phone_edit.clear()
            return
        self.name_edit.setText(items[0].text())
        self.phone_edit.setText(items[2].text())

    def save_supplier(self):
        name = self.name_edit.text().strip()
        if not name:
            return
        sup = self.session.query(Toptanci).filter_by(firma_adi=name).first()
        if not sup:
            sup = Toptanci(firma_adi=name)
            self.session.add(sup)

        sup.telefon = self.phone_edit.text().strip()
        self.session.commit()
        self.load_suppliers()

    def delete_supplier(self):
        name = self.name_edit.text().strip()
        sup = self.session.query(Toptanci).filter_by(firma_adi=name).first()
        if sup:
            self.session.delete(sup)
            self.session.commit()
            self.load_suppliers()

    def new_purchase(self):
        items = self.table.selectedItems()
        supplier = None
        if items:
            supplier = self.session.query(Toptanci).filter_by(
                firma_adi=items[0].text()
            ).first()
        self.purchase_win = PurchaseWindow(self.session, supplier)
        self.purchase_win.show()


class UserManagementWindow(QtWidgets.QWidget):
    """Personel yönetim penceresi."""

    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Personel İşlemleri")
        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.table = QtWidgets.QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Kullanıcı Adı", "Rol"])
        self.table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.table)

        form = QtWidgets.QFormLayout()
        self.user_edit = QtWidgets.QLineEdit()
        self.role_combo = QtWidgets.QComboBox()
        self.role_combo.addItems(["Admin", "Kasiyer"])
        self.pass_edit = QtWidgets.QLineEdit()
        self.pass_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        form.addRow("Kullanıcı Adı", self.user_edit)
        form.addRow("Rol", self.role_combo)
        form.addRow("Şifre", self.pass_edit)
        layout.addLayout(form)

        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_save = QtWidgets.QPushButton("Kaydet")
        self.btn_delete = QtWidgets.QPushButton("Sil")
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)

        self.btn_save.clicked.connect(self.save_user)
        self.btn_delete.clicked.connect(self.delete_user)
        self.table.itemSelectionChanged.connect(self.fill_form)

    def load_users(self):
        self.table.setRowCount(0)
        for u in self.session.query(Kullanici).all():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(u.kullanici_adi))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(u.rol))

    def fill_form(self):
        items = self.table.selectedItems()
        if not items:
            self.user_edit.clear()
            self.pass_edit.clear()
            self.role_combo.setCurrentIndex(1)
            return
        self.user_edit.setText(items[0].text())
        role = items[1].text()
        idx = self.role_combo.findText(role)
        if idx >= 0:
            self.role_combo.setCurrentIndex(idx)

    def save_user(self):
        name = self.user_edit.text().strip()
        if not name:
            return
        user = self.session.query(Kullanici).filter_by(kullanici_adi=name).first()
        if not user:
            user = Kullanici(kullanici_adi=name)
            self.session.add(user)
        pwd = self.pass_edit.text().strip()
        if pwd:
            user.sifre = hash_password(pwd)
        user.rol = self.role_combo.currentText()
        self.session.commit()
        self.pass_edit.clear()
        self.load_users()

    def delete_user(self):
        name = self.user_edit.text().strip()
        user = self.session.query(Kullanici).filter_by(kullanici_adi=name).first()
        if user:
            self.session.delete(user)
            self.session.commit()
            self.load_users()


class SettingsWindow(QtWidgets.QWidget):
    """Genel ayarları düzenleme penceresi."""

    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Genel Ayarlar")
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        self.edits = {}
        layout = QtWidgets.QFormLayout(self)
        for key in ["firma_adi", "adres", "telefon", "fis_alt_mesaj"]:
            edit = QtWidgets.QLineEdit()
            self.edits[key] = edit
            layout.addRow(key.replace("_", " ").title(), edit)
        btn = QtWidgets.QPushButton("Kaydet")
        layout.addRow(btn)
        btn.clicked.connect(self.save)

    def load_settings(self):
        for key, edit in self.edits.items():
            rec = self.session.query(Ayar).filter_by(ayar_adi=key).first()
            edit.setText(rec.ayar_degeri if rec else "")

    def save(self):
        for key, edit in self.edits.items():
            rec = self.session.query(Ayar).filter_by(ayar_adi=key).first()
            if rec:
                rec.ayar_degeri = edit.text().strip()
        self.session.commit()



class AdminWindow(QtWidgets.QWidget):
    """Yönetici menüsü."""

    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Yönetici Paneli")
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.btn_products = QtWidgets.QPushButton("Ürün İşlemleri")
        self.btn_customers = QtWidgets.QPushButton("Müşteri İşlemleri")
        self.btn_suppliers = QtWidgets.QPushButton("Toptancı İşlemleri")
        self.btn_finance = QtWidgets.QPushButton("Finans ve Raporlar")
        self.btn_users = QtWidgets.QPushButton("Personel İşlemleri")
        self.btn_settings = QtWidgets.QPushButton("Genel Ayarlar")
        self.btn_tools = QtWidgets.QPushButton("Yardımcı Araçlar")
        layout.addWidget(self.btn_products)
        layout.addWidget(self.btn_customers)
        layout.addWidget(self.btn_suppliers)
        layout.addWidget(self.btn_finance)
        layout.addWidget(self.btn_users)
        layout.addWidget(self.btn_settings)
        layout.addWidget(self.btn_tools)

        self.btn_products.clicked.connect(self.open_products)
        self.btn_customers.clicked.connect(self.open_customers)
        self.btn_suppliers.clicked.connect(self.open_suppliers)
        self.btn_finance.clicked.connect(self.open_finance)
        self.btn_users.clicked.connect(self.open_users)
        self.btn_settings.clicked.connect(self.open_settings)
        self.btn_tools.clicked.connect(self.open_tools)

    def open_products(self):
        self.product_win = ProductManagementWindow(self.session)
        self.product_win.show()

    def open_customers(self):
        self.customer_win = CustomerManagementWindow(self.session)
        self.customer_win.show()

    def open_suppliers(self):
        self.supplier_win = SupplierManagementWindow(self.session)
        self.supplier_win.show()

    def open_finance(self):
        self.finance_win = FinanceWindow(self.session)
        self.finance_win.show()

    def open_users(self):
        self.user_win = UserManagementWindow(self.session)
        self.user_win.show()

    def open_settings(self):
        self.settings_win = SettingsWindow(self.session)
        self.settings_win.show()

    def open_tools(self):
        self.tools_win = ToolsWindow()
        self.tools_win.show()


class CustomerSelectDialog(QtWidgets.QDialog):
    """Müşteri seçme penceresi."""

    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.selected_customer = None
        self.setWindowTitle("Müşteri Seç")
        self.setup_ui()
        self.load_customers()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("Ara...")
        layout.addWidget(self.search_edit)
        self.table = QtWidgets.QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Ad Soyad", "Telefon"])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        btn = QtWidgets.QPushButton("Seç")
        layout.addWidget(btn)
        btn.clicked.connect(self.accept_selection)
        self.table.doubleClicked.connect(self.accept_selection)
        self.search_edit.textChanged.connect(self.load_customers)

    def load_customers(self):
        query = self.session.query(Musteri)
        text = self.search_edit.text().strip()
        if text:
            query = query.filter(Musteri.ad_soyad.contains(text))
        customers = query.all()
        self.table.setRowCount(0)
        for cust in customers:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(cust.ad_soyad))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(cust.telefon or ""))

    def accept_selection(self):
        items = self.table.selectedItems()
        if not items:
            return
        ad = items[0].text()
        tel = items[1].text()
        self.selected_customer = (
            self.session.query(Musteri)
            .filter_by(ad_soyad=ad, telefon=tel)
            .first()
        )
        if self.selected_customer:
            self.accept()


class ExpenseDialog(QtWidgets.QDialog):
    """Basit gider ekleme penceresi."""

    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Gider Ekle")
        layout = QtWidgets.QFormLayout(self)
        self.desc_edit = QtWidgets.QLineEdit()
        self.amount_edit = QtWidgets.QDoubleSpinBox()
        self.amount_edit.setMaximum(9999999)
        layout.addRow("Açıklama", self.desc_edit)
        layout.addRow("Tutar", self.amount_edit)
        btn = QtWidgets.QPushButton("Kaydet")
        layout.addWidget(btn)
        btn.clicked.connect(self.save)

    def save(self):
        desc = self.desc_edit.text().strip()
        amount = float(self.amount_edit.value())
        if not desc or amount == 0:
            self.reject()
            return
        self.session.add(Gider(aciklama=desc, tutar=amount))
        self.session.commit()
        self.accept()


class CashDialog(QtWidgets.QDialog):
    """Tahsilat veya tediye işlemi."""

    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.selected_customer = None
        self.setWindowTitle("Tahsilat/Tediye Yap")
        layout = QtWidgets.QFormLayout(self)
        cust_layout = QtWidgets.QHBoxLayout()
        self.cust_label = QtWidgets.QLabel("-")
        select_btn = QtWidgets.QPushButton("Müşteri Seç")
        select_btn.clicked.connect(self.select_customer)
        cust_layout.addWidget(self.cust_label)
        cust_layout.addWidget(select_btn)
        layout.addRow("Müşteri", cust_layout)
        self.amount_edit = QtWidgets.QDoubleSpinBox()
        self.amount_edit.setMaximum(9999999)
        self.amount_edit.setMinimum(-9999999)
        self.desc_edit = QtWidgets.QLineEdit()
        layout.addRow("Tutar (+Tahsilat,-Tediye)", self.amount_edit)
        layout.addRow("Açıklama", self.desc_edit)
        btn = QtWidgets.QPushButton("Kaydet")
        layout.addWidget(btn)
        btn.clicked.connect(self.save)

    def select_customer(self):
        dlg = CustomerSelectDialog(self.session)
        if (
            dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted
            and dlg.selected_customer
        ):
            self.selected_customer = dlg.selected_customer
            self.cust_label.setText(self.selected_customer.ad_soyad)

    def save(self):
        if not self.selected_customer:
            QtWidgets.QMessageBox.warning(self, "Hata", "Müşteri seçin")
            return
        amount = float(self.amount_edit.value())
        hareket = CariHareket(
            musteri_id=self.selected_customer.id,
            tutar=amount,
            aciklama=self.desc_edit.text().strip() or "Tahsilat",
        )
        self.session.add(hareket)
        self.selected_customer.bakiye -= amount
        self.session.commit()
        self.accept()


class ReportDialog(QtWidgets.QDialog):
    """Gün sonu raporu penceresi."""

    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Gün Sonu Raporu")
        layout = QtWidgets.QVBoxLayout(self)
        top = QtWidgets.QHBoxLayout()
        top.addWidget(QtWidgets.QLabel("Tarih:"))
        self.date_edit = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        top.addWidget(self.date_edit)
        self.calc_btn = QtWidgets.QPushButton("Hesapla")
        top.addWidget(self.calc_btn)
        layout.addLayout(top)
        self.result = QtWidgets.QTextEdit()
        self.result.setReadOnly(True)
        layout.addWidget(self.result)
        self.calc_btn.clicked.connect(self.calculate)

    def calculate(self):
        date = self.date_edit.date().toPyDate()
        start = datetime.combine(date, datetime.min.time())
        end = datetime.combine(date, datetime.max.time())
        q = self.session.query(SatisKaydi).filter(
            SatisKaydi.tarih >= start, SatisKaydi.tarih <= end
        )
        toplam_nakit = sum(
            s.toplam_tutar
            for s in q.filter(SatisKaydi.odeme_tipi == "Nakit", SatisKaydi.musteri_id == None)
        )
        toplam_kart = sum(
            s.toplam_tutar
            for s in q.filter(
                SatisKaydi.odeme_tipi == "Kredi Kartı", SatisKaydi.musteri_id == None
            )
        )
        toplam_veresiye = sum(
            s.toplam_tutar for s in q.filter(SatisKaydi.musteri_id != None)
        )
        toplam_tahsilat = sum(
            h.tutar
            for h in self.session.query(CariHareket)
            .filter(CariHareket.tarih >= start, CariHareket.tarih <= end, CariHareket.tutar > 0)
        )
        toplam_gider = sum(
            g.tutar
            for g in self.session.query(Gider)
            .filter(Gider.tarih >= start, Gider.tarih <= end)
        )
        kasa_nakit = (toplam_nakit + toplam_tahsilat) - toplam_gider

        lines = [
            f"Toplam Nakit Satış: {toplam_nakit:.2f}",
            f"Toplam K. Kartı Satış: {toplam_kart:.2f}",
            f"Toplam Veresiye Satış: {toplam_veresiye:.2f}",
            f"Toplam Tahsilat: {toplam_tahsilat:.2f}",
            f"Toplam Gider: {toplam_gider:.2f}",
            f"KASADAKİ NAKİT: {kasa_nakit:.2f}",
        ]
        self.result.setPlainText("\n".join(lines))


class AdvancedReportsDialog(QtWidgets.QDialog):
    """Gelişmiş raporlar"""

    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Gelişmiş Raporlar")
        layout = QtWidgets.QVBoxLayout(self)
        range_layout = QtWidgets.QHBoxLayout()
        range_layout.addWidget(QtWidgets.QLabel("Başlangıç:"))
        self.start_edit = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
        self.start_edit.setCalendarPopup(True)
        range_layout.addWidget(self.start_edit)
        range_layout.addWidget(QtWidgets.QLabel("Bitiş:"))
        self.end_edit = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
        self.end_edit.setCalendarPopup(True)
        range_layout.addWidget(self.end_edit)
        layout.addLayout(range_layout)

        self.tabs = QtWidgets.QTabWidget()
        layout.addWidget(self.tabs)

        self.txt_profit = QtWidgets.QTextEdit()
        self.txt_profit.setReadOnly(True)
        self.tabs.addTab(self.txt_profit, "Kâr/Zarar")

        self.tbl_product = QtWidgets.QTableWidget(0, 6)
        self.tbl_product.setHorizontalHeaderLabels([
            "Ürün", "Adet", "Gelir", "Maliyet", "Kâr", "Kâr %",
        ])
        self.tbl_product.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.tabs.addTab(self.tbl_product, "Ürün Bazında")

        self.tbl_best = QtWidgets.QTableWidget(0, 2)
        self.tbl_best.setHorizontalHeaderLabels(["Ürün", "Adet"])
        self.tbl_best.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.tabs.addTab(self.tbl_best, "En Çok Satan")

        self.txt_stock = QtWidgets.QTextEdit()
        self.txt_stock.setReadOnly(True)
        self.tabs.addTab(self.txt_stock, "Stok Değeri")

        btn = QtWidgets.QPushButton("Hesapla")
        layout.addWidget(btn)
        btn.clicked.connect(self.calculate)

    def calculate(self):
        start = datetime.combine(
            self.start_edit.date().toPyDate(), datetime.min.time()
        )
        end = datetime.combine(self.end_edit.date().toPyDate(), datetime.max.time())

        kalemler = (
            self.session.query(SatisKalem)
            .join(SatisKaydi)
            .filter(SatisKaydi.tarih >= start, SatisKaydi.tarih <= end)
            .all()
        )
        gelir = sum(k.birim_satis_fiyati * k.adet for k in kalemler)
        maliyet = sum(k.birim_alis_fiyati * k.adet for k in kalemler)
        brut = gelir - maliyet
        gider = sum(
            g.tutar
            for g in self.session.query(Gider).filter(Gider.tarih >= start, Gider.tarih <= end)
        )
        net = brut - gider
        marj = (net / gelir * 100) if gelir else 0
        lines = [
            f"Toplam Gelir: {gelir:.2f}",
            f"SMM: {maliyet:.2f}",
            f"Brüt Kâr: {brut:.2f}",
            f"Toplam Giderler: {gider:.2f}",
            f"Net Kâr: {net:.2f}",
            f"Net Kâr Marjı: {marj:.2f}%",
        ]
        self.txt_profit.setPlainText("\n".join(lines))

        # Ürün bazında kâr
        from sqlalchemy import func

        rows = (
            self.session.query(
                Urun.urun_adi,
                func.sum(SatisKalem.adet),
                func.sum(SatisKalem.adet * SatisKalem.birim_satis_fiyati),
                func.sum(SatisKalem.adet * SatisKalem.birim_alis_fiyati),
            )
            .join(SatisKalem)
            .join(SatisKaydi)
            .filter(SatisKaydi.tarih >= start, SatisKaydi.tarih <= end)
            .group_by(Urun.id)
            .all()
        )
        self.tbl_product.setRowCount(0)
        for r in rows:
            adet = r[1] or 0
            gelir_p = r[2] or 0
            maliyet_p = r[3] or 0
            kar = gelir_p - maliyet_p
            kar_m = (kar / gelir_p * 100) if gelir_p else 0
            row = self.tbl_product.rowCount()
            self.tbl_product.insertRow(row)
            self.tbl_product.setItem(row, 0, QtWidgets.QTableWidgetItem(r[0]))
            self.tbl_product.setItem(row, 1, QtWidgets.QTableWidgetItem(str(int(adet))))
            self.tbl_product.setItem(row, 2, QtWidgets.QTableWidgetItem(f"{gelir_p:.2f}"))
            self.tbl_product.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{maliyet_p:.2f}"))
            self.tbl_product.setItem(row, 4, QtWidgets.QTableWidgetItem(f"{kar:.2f}"))
            self.tbl_product.setItem(row, 5, QtWidgets.QTableWidgetItem(f"{kar_m:.2f}%"))

        self.tbl_product.sortItems(5, QtCore.Qt.SortOrder.DescendingOrder)

        # En çok satanlar
        best_rows = (
            self.session.query(
                Urun.urun_adi,
                func.sum(SatisKalem.adet).label('adet')
            )
            .join(SatisKalem)
            .join(SatisKaydi)
            .filter(SatisKaydi.tarih >= start, SatisKaydi.tarih <= end)
            .group_by(Urun.id)
            .order_by(func.sum(SatisKalem.adet).desc())
            .all()
        )
        self.tbl_best.setRowCount(0)
        for r in best_rows:
            row = self.tbl_best.rowCount()
            self.tbl_best.insertRow(row)
            self.tbl_best.setItem(row, 0, QtWidgets.QTableWidgetItem(r[0]))
            self.tbl_best.setItem(row, 1, QtWidgets.QTableWidgetItem(str(int(r[1]))))

        # Stok değeri
        stock_total = sum(u.stok_miktari * u.alis_fiyati for u in self.session.query(Urun))
        lines = [f"Toplam Stok Değeri: {stock_total:.2f}"]
        self.txt_stock.setPlainText("\n".join(lines))


class PurchaseWindow(QtWidgets.QWidget):
    """Yeni mal alımı penceresi."""

    def __init__(self, session: Session, supplier: Toptanci | None = None):
        super().__init__()
        self.session = session
        self.pending_qty = 1
        self.purchase_items: dict[str, dict] = {}
        self.setWindowTitle("Mal Alımı")
        self.setup_ui()
        self.load_suppliers()
        if supplier:
            index = self.supplier_combo.findText(supplier.firma_adi)
            if index >= 0:
                self.supplier_combo.setCurrentIndex(index)

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        form = QtWidgets.QFormLayout()
        self.supplier_combo = QtWidgets.QComboBox()
        self.invoice_edit = QtWidgets.QLineEdit()
        form.addRow("Toptancı", self.supplier_combo)
        form.addRow("Fatura No", self.invoice_edit)
        layout.addLayout(form)

        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            "Ürün",
            "Adet",
            "Alış Fiyatı",
            "Toplam",
        ])
        self.table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.table)

        self.barcode_edit = QtWidgets.QLineEdit()
        self.barcode_edit.setPlaceholderText("Barkod")
        self.barcode_edit.returnPressed.connect(self.on_barcode_entered)
        layout.addWidget(self.barcode_edit)

        self.total_label = QtWidgets.QLabel("0.00")
        font = self.total_label.font()
        font.setPointSize(14)
        self.total_label.setFont(font)
        layout.addWidget(self.total_label)

        self.btn_finish = QtWidgets.QPushButton("Alımı Tamamla")
        layout.addWidget(self.btn_finish)
        self.btn_finish.clicked.connect(self.finish_purchase)

    def load_suppliers(self):
        self.supplier_combo.clear()
        for sup in self.session.query(Toptanci).all():
            self.supplier_combo.addItem(sup.firma_adi, sup)

    def on_barcode_entered(self):
        text = self.barcode_edit.text().strip()
        self.barcode_edit.clear()
        if text.startswith("*"):
            try:
                self.pending_qty = int(text[1:])
            except ValueError:
                self.pending_qty = 1
            return

        product = self.session.query(Urun).filter_by(barkod=text).first()
        if not product:
            QtWidgets.QMessageBox.warning(self, "Hata", "Ürün bulunamadı")
            self.pending_qty = 1
            return

        price, ok = QtWidgets.QInputDialog.getDouble(
            self,
            "Alış Fiyatı",
            "Birim alış fiyatı",
            product.alis_fiyati or product.fiyat,
            0,
            999999,
            2,
        )
        if not ok:
            self.pending_qty = 1
            return
        self.add_product(product, self.pending_qty, price)
        self.pending_qty = 1

    def add_product(self, product: Urun, qty: int, price: float):
        if product.barkod in self.purchase_items:
            row = self.purchase_items[product.barkod]["row"]
            current_qty = self.purchase_items[product.barkod]["qty"] + qty
            self.purchase_items[product.barkod]["qty"] = current_qty
            self.purchase_items[product.barkod]["price"] = price
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(current_qty)))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(f"{price:.2f}"))
            self.table.setItem(
                row, 3, QtWidgets.QTableWidgetItem(f"{current_qty * price:.2f}")
            )
        else:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(product.urun_adi))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(qty)))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(f"{price:.2f}"))
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{price * qty:.2f}"))
            self.purchase_items[product.barkod] = {
                "row": row,
                "qty": qty,
                "price": price,
                "product": product,
            }
        self.update_total()

    def update_total(self):
        total = sum(v["price"] * v["qty"] for v in self.purchase_items.values())
        self.total_label.setText(f"{total:.2f}")

    def finish_purchase(self):
        sup: Toptanci = self.supplier_combo.currentData()
        if not sup:
            QtWidgets.QMessageBox.warning(self, "Hata", "Toptancı seçin")
            return
        if not self.purchase_items:
            return
        total = sum(v["price"] * v["qty"] for v in self.purchase_items.values())
        mal = MalAlimi(
            toptanci_id=sup.id,
            fatura_no=self.invoice_edit.text().strip(),
            toplam_tutar=total,
        )
        self.session.add(mal)
        for item in self.purchase_items.values():
            product: Urun = item["product"]
            qty = item["qty"]
            price = item["price"]
            det = MalAlimiDetay(
                mal_alimi=mal,
                urun_id=product.id,
                adet=qty,
                birim_alis_fiyati=price,
            )
            self.session.add(det)
            product.stok_miktari += qty
            product.alis_fiyati = price
        sup.bakiye += total
        self.session.commit()
        self.close()


class FinanceWindow(QtWidgets.QWidget):
    """Finans işlemleri ve raporlar."""

    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Finans ve Raporlar")
        layout = QtWidgets.QVBoxLayout(self)
        self.btn_expense = QtWidgets.QPushButton("Gider Ekle")
        self.btn_cash = QtWidgets.QPushButton("Tahsilat/Tediye Yap")
        self.btn_report = QtWidgets.QPushButton("Gün Sonu Raporu")
        self.btn_adv_report = QtWidgets.QPushButton("Gelişmiş Raporlar")
        layout.addWidget(self.btn_expense)
        layout.addWidget(self.btn_cash)
        layout.addWidget(self.btn_report)
        layout.addWidget(self.btn_adv_report)
        self.btn_expense.clicked.connect(self.add_expense)
        self.btn_cash.clicked.connect(self.add_cash)
        self.btn_report.clicked.connect(self.show_report)
        self.btn_adv_report.clicked.connect(self.show_advanced)

    def add_expense(self):
        dlg = ExpenseDialog(self.session)
        dlg.exec()

    def add_cash(self):
        dlg = CashDialog(self.session)
        dlg.exec()

    def show_report(self):
        dlg = ReportDialog(self.session)
        dlg.exec()

    def show_advanced(self):
        dlg = AdvancedReportsDialog(self.session)
        dlg.exec()


class ToolsWindow(QtWidgets.QWidget):
    """Yedekleme ve geri yükleme araçları."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yardımcı Araçlar")
        layout = QtWidgets.QVBoxLayout(self)
        self.btn_backup = QtWidgets.QPushButton("Yedekle")
        self.btn_restore = QtWidgets.QPushButton("Geri Yükle")
        layout.addWidget(self.btn_backup)
        layout.addWidget(self.btn_restore)
        self.btn_backup.clicked.connect(self.backup)
        self.btn_restore.clicked.connect(self.restore)

    def backup(self):
        db_path = Path(DB_URL.split("///")[-1])
        backup_dir = Path("yedekler")
        backup_dir.mkdir(exist_ok=True)
        name = datetime.now().strftime("yedek_%d-%m-%Y_%H-%M.db")
        shutil.copy(db_path, backup_dir / name)
        QtWidgets.QMessageBox.information(self, "Yedek", "Yedekleme başarıyla tamamlandı")

    def restore(self):
        backup_dir = Path("yedekler")
        backup_dir.mkdir(exist_ok=True)
        files = [f.name for f in backup_dir.glob("*.db")]
        if not files:
            QtWidgets.QMessageBox.information(self, "Geri Yükle", "Yedek bulunamadı")
            return
        file, ok = QtWidgets.QInputDialog.getItem(self, "Geri Yükle", "Dosya seç", files, 0, False)
        if not ok:
            return
        reply = QtWidgets.QMessageBox.question(
            self,
            "Onay",
            "UYARI: Bu işlem tüm mevcut verileri silecek ve seçili yedekle değiştirecektir. Emin misiniz?",
        )
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        db_path = Path(DB_URL.split("///")[-1])
        shutil.copy(backup_dir / file, db_path)
        QtWidgets.QMessageBox.information(self, "Geri Yükle", "Geri yükleme tamamlandı. Programı yeniden başlatın.")


class MainWindow(QtWidgets.QWidget):
    """Ana POS ekranı."""

    def __init__(self, user: Kullanici):
        super().__init__()
        self.user = user
        self.setWindowTitle("POS")
        self.pending_qty = 1
        self.payment_type = "Nakit"
        self.session = Session()
        self.sale_items = {}
        self.selected_customer = None
        self.setup_ui()

    def setup_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        content_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(content_layout)

        # Sol taraftaki tablo
        self.table = SaleTable()
        content_layout.addWidget(self.table)

        # Sağ taraftaki boş alan (hızlı ürün butonları için)
        self.fast_buttons = QtWidgets.QWidget()
        content_layout.addWidget(self.fast_buttons)

        # Barkod giriş kutusu
        self.barcode_edit = QtWidgets.QLineEdit()
        self.barcode_edit.returnPressed.connect(self.on_barcode_entered)
        main_layout.addWidget(self.barcode_edit)

        # Toplam tutar etiketi
        self.total_label = QtWidgets.QLabel("0.00")
        font = self.total_label.font()
        font.setPointSize(16)
        self.total_label.setFont(font)
        main_layout.addWidget(self.total_label)

        # Seçili müşteri etiketi
        self.customer_label = QtWidgets.QLabel("Müşteri: -")
        main_layout.addWidget(self.customer_label)

        # Alt butonlar
        btn_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(btn_layout)

        self.btn_nakit = QtWidgets.QPushButton("[F1] NAKİT SATIŞ")
        self.btn_kart = QtWidgets.QPushButton("[F3] K. KARTLI SATIŞ")
        self.btn_customer = QtWidgets.QPushButton("[F4] Müşteri Seç")
        self.btn_admin = QtWidgets.QPushButton("[F6] YÖNETİCİ")
        self.btn_print_receipt = QtWidgets.QPushButton("[F12] Yazdır")

        btn_layout.addWidget(self.btn_nakit)
        btn_layout.addWidget(self.btn_kart)
        btn_layout.addWidget(self.btn_admin)
        btn_layout.insertWidget(2, self.btn_customer)
        btn_layout.addWidget(self.btn_print_receipt)

        self.btn_nakit.clicked.connect(self.finish_sale_nakit)
        self.btn_kart.clicked.connect(self.start_kart_sale)
        self.btn_admin.clicked.connect(self.open_admin)
        self.btn_customer.clicked.connect(self.select_customer)
        self.btn_print_receipt.clicked.connect(self.print_receipt)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key.Key_F1:
            self.finish_sale_nakit()
        elif event.key() == QtCore.Qt.Key.Key_F3:
            self.start_kart_sale()
        elif event.key() == QtCore.Qt.Key.Key_F4:
            self.select_customer()
        elif event.key() == QtCore.Qt.Key.Key_F6:
            self.open_admin()
        elif event.key() == QtCore.Qt.Key.Key_F12:
            self.print_receipt()
        else:
            super().keyPressEvent(event)

    def on_barcode_entered(self):
        text = self.barcode_edit.text().strip()
        self.barcode_edit.clear()
        # Miktar tanımlandı mı?
        if text.startswith("*"):
            try:
                self.pending_qty = int(text[1:])
            except ValueError:
                self.pending_qty = 1
            return

        # Ürünü bul
        product = self.session.query(Urun).filter_by(barkod=text).first()
        if not product:
            QtWidgets.QMessageBox.warning(self, "Hata", "Ürün bulunamadı")
            self.pending_qty = 1
            return

        self.add_product(product, self.pending_qty)
        self.pending_qty = 1

    def add_product(self, product: Urun, qty: int):
        """Ürünü tabloya ekle veya adetini artır."""
        if product.barkod in self.sale_items:
            row = self.sale_items[product.barkod]["row"]
            current_qty = self.sale_items[product.barkod]["qty"] + qty
            self.sale_items[product.barkod]["qty"] = current_qty
            self.table.setItem(
                row, 1, QtWidgets.QTableWidgetItem(str(current_qty))
            )
            toplam = product.fiyat * current_qty
            self.table.setItem(
                row, 3, QtWidgets.QTableWidgetItem(f"{toplam:.2f}")
            )
        else:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(
                row, 0, QtWidgets.QTableWidgetItem(product.urun_adi)
            )
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(qty)))
            self.table.setItem(
                row, 2, QtWidgets.QTableWidgetItem(f"{product.fiyat:.2f}")
            )
            self.table.setItem(
                row, 3, QtWidgets.QTableWidgetItem(f"{product.fiyat * qty:.2f}")
            )
            self.sale_items[product.barkod] = {
                "row": row,
                "qty": qty,
                "product": product,
            }
        self.update_total()

    def update_total(self):
        total = sum(v['product'].fiyat * v['qty'] for v in self.sale_items.values())
        self.total_label.setText(f"{total:.2f}")

    def clear_sale(self):
        self.table.setRowCount(0)
        self.sale_items.clear()
        self.update_total()
        self.selected_customer = None
        self.customer_label.setText("Müşteri: -")

    def finish_sale_nakit(self):
        """Satışı nakit olarak bitirir."""
        self.payment_type = "Nakit" if self.payment_type == "Nakit" else self.payment_type
        total = sum(v['product'].fiyat * v['qty'] for v in self.sale_items.values())
        for item in self.sale_items.values():
            urun = item['product']
            urun.stok_miktari -= item['qty']
        sale = SatisKaydi(
            odeme_tipi=self.payment_type if not self.selected_customer else "Veresiye",
            toplam_tutar=total,
            musteri_id=self.selected_customer.id if self.selected_customer else None,
        )
        self.session.add(sale)
        for item in self.sale_items.values():
            urun = item['product']
            kalem = SatisKalem(
                satis=sale,
                urun_id=urun.id,
                adet=item['qty'],
                birim_satis_fiyati=urun.fiyat,
                birim_alis_fiyati=urun.alis_fiyati,
            )
            self.session.add(kalem)
        if self.selected_customer:
            self.selected_customer.bakiye += total
        self.session.commit()
        self.clear_sale()
        self.payment_type = "Nakit"

    def start_kart_sale(self):
        self.payment_type = "Kredi Kartı"
        QtWidgets.QMessageBox.information(self, "Satış", "Satış Kredi Kartı olarak işaretlendi. F1 ile tamamlayın")

    def select_customer(self):
        dlg = CustomerSelectDialog(self.session)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted and dlg.selected_customer:
            self.selected_customer = dlg.selected_customer
            self.customer_label.setText(f"Müşteri: {self.selected_customer.ad_soyad}")
        else:
            self.selected_customer = None
            self.customer_label.setText("Müşteri: -")

    def print_receipt(self):
        settings = {s.ayar_adi: s.ayar_degeri for s in self.session.query(Ayar).all()}
        lines = [
            settings.get("firma_adi", ""),
            settings.get("adres", ""),
            settings.get("telefon", ""),
            "-" * 30,
        ]
        for item in self.sale_items.values():
            p = item["product"]
            qty = item["qty"]
            lines.append(f"{p.urun_adi} x{qty} = {p.fiyat * qty:.2f}")
        lines.append("-" * 30)
        lines.append(f"Toplam: {self.total_label.text()}")
        if settings.get("fis_alt_mesaj"):
            lines.append(settings.get("fis_alt_mesaj"))
        text = "\n".join(lines)
        QtWidgets.QMessageBox.information(self, "Fiş", text)

    def open_admin(self):
        if self.user.rol != "Admin":
            QtWidgets.QMessageBox.warning(self, "Yetki", "Bu bölüme erişiminiz yok")
            return
        self.admin_win = AdminWindow(self.session)
        self.admin_win.show()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    login = LoginWindow()
    if login.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        window = MainWindow(login.result)
        window.show()
        sys.exit(app.exec())

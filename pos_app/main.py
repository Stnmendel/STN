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

from .models import Base, Kullanici, Urun

DB_URL = "sqlite:///pos.db"

engine = create_engine(DB_URL, echo=False)
Session = sessionmaker(bind=engine)

# Veritabanını oluştur
Base.metadata.create_all(engine)

# Varsayılan admin kullanıcısını ekle
session = Session()
if not session.query(Kullanici).filter_by(kullanici_adi="Admin").first():
    hashed = hashlib.sha256("1".encode()).hexdigest()
    admin = Kullanici(kullanici_adi="Admin", sifre=hashed)
    session.add(admin)
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
        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Barkod", "Ürün Adı", "Fiyat", "Stok"])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        form = QtWidgets.QFormLayout()
        self.barcode_edit = QtWidgets.QLineEdit()
        self.name_edit = QtWidgets.QLineEdit()
        self.price_edit = QtWidgets.QDoubleSpinBox()
        self.price_edit.setMaximum(999999)
        self.stock_edit = QtWidgets.QSpinBox()
        self.stock_edit.setMaximum(999999)
        form.addRow("Barkod", self.barcode_edit)
        form.addRow("Ürün Adı", self.name_edit)
        form.addRow("Fiyat", self.price_edit)
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
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(product.stok_miktari)))

    def fill_form(self):
        items = self.table.selectedItems()
        if not items:
            self.barcode_edit.clear()
            self.name_edit.clear()
            self.price_edit.setValue(0)
            self.stock_edit.setValue(0)
            return
        self.barcode_edit.setText(items[0].text())
        self.name_edit.setText(items[1].text())
        self.price_edit.setValue(float(items[2].text()))
        self.stock_edit.setValue(int(items[3].text()))

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
        self.btn_reports = QtWidgets.QPushButton("Raporlar")
        self.btn_settings = QtWidgets.QPushButton("Ayarlar")
        layout.addWidget(self.btn_products)
        layout.addWidget(self.btn_customers)
        layout.addWidget(self.btn_reports)
        layout.addWidget(self.btn_settings)

        self.btn_products.clicked.connect(self.open_products)

    def open_products(self):
        self.product_win = ProductManagementWindow(self.session)
        self.product_win.show()


class MainWindow(QtWidgets.QWidget):
    """Ana POS ekranı."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("POS")
        self.pending_qty = 1
        self.payment_type = "Nakit"
        self.session = Session()
        self.sale_items = {}
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

        # Alt butonlar
        btn_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(btn_layout)

        self.btn_nakit = QtWidgets.QPushButton("[F1] NAKİT SATIŞ")
        self.btn_kart = QtWidgets.QPushButton("[F3] K. KARTLI SATIŞ")
        self.btn_admin = QtWidgets.QPushButton("[F6] YÖNETİCİ")

        btn_layout.addWidget(self.btn_nakit)
        btn_layout.addWidget(self.btn_kart)
        btn_layout.addWidget(self.btn_admin)

        self.btn_nakit.clicked.connect(self.finish_sale_nakit)
        self.btn_kart.clicked.connect(self.start_kart_sale)
        self.btn_admin.clicked.connect(self.open_admin)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key.Key_F1:
            self.finish_sale_nakit()
        elif event.key() == QtCore.Qt.Key.Key_F3:
            self.start_kart_sale()
        elif event.key() == QtCore.Qt.Key.Key_F6:
            self.open_admin()
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

    def finish_sale_nakit(self):
        """Satışı nakit olarak bitirir."""
        self.payment_type = "Nakit" if self.payment_type == "Nakit" else self.payment_type
        for item in self.sale_items.values():
            urun = item['product']
            urun.stok_miktari -= item['qty']
        self.session.commit()
        self.clear_sale()
        self.payment_type = "Nakit"

    def start_kart_sale(self):
        self.payment_type = "Kredi Kartı"
        QtWidgets.QMessageBox.information(self, "Satış", "Satış Kredi Kartı olarak işaretlendi. F1 ile tamamlayın")

    def open_admin(self):
        self.admin_win = AdminWindow(self.session)
        self.admin_win.show()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    login = LoginWindow()
    if login.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        window = MainWindow()
        window.show()
        sys.exit(app.exec())

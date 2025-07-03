import sys
import hashlib

from PyQt6 import QtCore, QtGui, QtWidgets
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

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key.Key_F1:
            self.finish_sale_nakit()
        elif event.key() == QtCore.Qt.Key.Key_F3:
            self.start_kart_sale()
        elif event.key() == QtCore.Qt.Key.Key_F6:
            QtWidgets.QMessageBox.information(self, "Yönetici", "Yönetici modu")
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
            row = self.sale_items[product.barkod]['row']
            current_qty = self.sale_items[product.barkod]['qty'] + qty
            self.sale_items[product.barkod]['qty'] = current_qty
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(current_qty)))
            toplam = product.fiyat * current_qty
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{toplam:.2f}"))
        else:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(product.urun_adi))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(qty)))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(f"{product.fiyat:.2f}"))
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{product.fiyat * qty:.2f}"))
            self.sale_items[product.barkod] = {"row": row, "qty": qty, "product": product}
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


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    login = LoginWindow()
    if login.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        window = MainWindow()
        window.show()
        sys.exit(app.exec())

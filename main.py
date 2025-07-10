from PyQt6 import QtWidgets
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QMessageBox,
    QHBoxLayout,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
)
from PyQt6.QtGui import QKeySequence, QShortcut
import hashlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Kullanici, Urun

DB_URL = "sqlite:///pos.db"
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

# Create a default Admin user if not present
session = Session()
if not session.query(Kullanici).filter_by(kullanici_adi="Admin").first():
    admin = Kullanici(
        kullanici_adi="Admin",
        sifre=hash_password("1"),
        rol="Admin",
    )
    session.add(admin)
    session.commit()
session.close()


class AdminWindow(QWidget):
    """Simple admin panel with a button for product operations."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yönetici Paneli")
        layout = QVBoxLayout(self)
        self.product_button = QPushButton("Ürün İşlemleri")
        self.product_button.clicked.connect(self.open_product_management)
        layout.addWidget(self.product_button)

    def open_product_management(self):
        self.product_window = ProductManagementWindow()
        self.product_window.show()


class ProductManagementWindow(QWidget):
    """Window to list and create products."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ürün Yönetimi")

        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Barkod", "Ürün Adı", "Fiyat", "Stok"])
        layout.addWidget(self.table)

        form_layout = QFormLayout()
        self.barcode_edit = QLineEdit()
        self.name_edit = QLineEdit()
        self.price_edit = QLineEdit()
        self.stock_edit = QLineEdit()
        form_layout.addRow("Barkod", self.barcode_edit)
        form_layout.addRow("Ürün Adı", self.name_edit)
        form_layout.addRow("Fiyat", self.price_edit)
        form_layout.addRow("Stok", self.stock_edit)
        layout.addLayout(form_layout)

        self.save_button = QPushButton("Kaydet")
        self.save_button.clicked.connect(self.save_product)
        layout.addWidget(self.save_button)

        self.load_products()

    def load_products(self):
        """Load products from the database into the table."""
        session = Session()
        products = session.query(Urun).all()
        session.close()

        self.table.setRowCount(0)
        for product in products:
            self._add_product_to_table(product)

    def _add_product_to_table(self, product: Urun):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(product.barkod))
        self.table.setItem(row, 1, QTableWidgetItem(product.urun_adi))
        self.table.setItem(row, 2, QTableWidgetItem(f"{product.fiyat:.2f}"))
        self.table.setItem(row, 3, QTableWidgetItem(str(product.stok_miktari)))

    def save_product(self):
        """Save a new product to the database and refresh the table."""
        try:
            price = float(self.price_edit.text())
            stock = int(self.stock_edit.text())
        except ValueError:
            QMessageBox.warning(self, "Hata", "Fiyat veya stok değeri geçersiz")
            return

        product = Urun(
            barkod=self.barcode_edit.text(),
            urun_adi=self.name_edit.text(),
            fiyat=price,
            stok_miktari=stock,
        )

        session = Session()
        session.add(product)
        session.commit()
        session.close()

        self._add_product_to_table(product)
        self.barcode_edit.clear()
        self.name_edit.clear()
        self.price_edit.clear()
        self.stock_edit.clear()


class MainWindow(QtWidgets.QWidget):
    def __init__(self, user: Kullanici, parent=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle(f"Barkomatik POS - {user.kullanici_adi} ({user.rol})")
        self.resize(800, 600)
        self.session = Session()
        self.sale_items = {}
        self.sub_windows = {}
        self.pending_qty = 1
        self.setup_ui()
        self.setup_shortcuts()

    def setup_ui(self):
        """Create the main sales screen layout."""
        main_layout = QHBoxLayout(self)

        # Left side layout containing the sales table and controls
        left_layout = QVBoxLayout()
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Ürün Adı", "Adet", "Fiyat", "Toplam"])
        left_layout.addWidget(self.table)

        self.barcode_edit = QLineEdit()
        self.barcode_edit.returnPressed.connect(self.on_barcode_entered)
        left_layout.addWidget(self.barcode_edit)

        self.total_label = QLabel("0")
        font = self.total_label.font()
        font.setPointSize(24)
        self.total_label.setFont(font)
        left_layout.addWidget(self.total_label)

        button_layout = QHBoxLayout()
        self.finish_button = QPushButton("[F1] SATIŞI BİTİR")
        self.manager_button = QPushButton("[F6] YÖNETİCİ")
        self.manager_button.clicked.connect(self.open_admin)
        button_layout.addWidget(self.finish_button)
        button_layout.addWidget(self.manager_button)
        left_layout.addLayout(button_layout)

        main_layout.addLayout(left_layout)

        # Placeholder right side for future widgets
        main_layout.addStretch()

    def setup_shortcuts(self):
        """Define keyboard shortcuts for quick actions."""
        finish_sc = QShortcut(QKeySequence("F1"), self)
        finish_sc.activated.connect(self.finish_sale)
        admin_sc = QShortcut(QKeySequence("F6"), self)
        admin_sc.activated.connect(self.open_admin)

    def on_barcode_entered(self):
        """Handle barcode input and add the product to the sale."""
        barcode = self.barcode_edit.text().strip()
        self.barcode_edit.clear()
        if not barcode:
            return

        product = self.session.query(Urun).filter_by(barkod=barcode).first()

        if not product:
            QMessageBox.warning(self, "Hata", "Ürün bulunamadı")
            return

        self.add_product_to_sale(product)

    def add_product_to_sale(self, product: Urun):
        """Add a product to the sales table or increase its quantity."""
        if product.barkod in self.sale_items:
            data = self.sale_items[product.barkod]
            data["quantity"] += 1
            row = data["row"]
            self.table.item(row, 1).setText(str(data["quantity"]))
            total = data["quantity"] * data["price"]
            self.table.item(row, 3).setText(f"{total:.2f}")
        else:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(product.urun_adi))
            self.table.setItem(row, 1, QTableWidgetItem("1"))
            self.table.setItem(row, 2, QTableWidgetItem(f"{product.fiyat:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{product.fiyat:.2f}"))
            self.sale_items[product.barkod] = {
                "row": row,
                "quantity": 1,
                "price": product.fiyat,
                "product": product,
            }

        self.update_total()

    def update_total(self):
        """Update the total label based on current sale items."""
        total = sum(item["quantity"] * item["price"] for item in self.sale_items.values())
        self.total_label.setText(f"{total:.2f} TL")

    def finish_sale(self):
        """Complete the sale and reset the table."""
        self.sale_items.clear()
        self.table.setRowCount(0)
        self.update_total()

    def open_admin(self):
        """Open the admin panel."""
        self.admin_window = AdminWindow()
        self.admin_window.show()


class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Giris")

        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_button = QPushButton("Giris")
        self.login_button.clicked.connect(self.try_login)

        layout = QFormLayout(self)
        layout.addRow("Kullanici Adi", self.username_input)
        layout.addRow("Sifre", self.password_input)
        layout.addWidget(self.login_button)

    def try_login(self):
        session = Session()
        user = (
            session.query(Kullanici)
            .filter_by(
                kullanici_adi=self.username_input.text(),
                sifre=hash_password(self.password_input.text()),
            )
            .first()
        )
        session.close()

        if user:
            self.user = user
            self.accept()
        else:
            QMessageBox.warning(self, "Hata", "Kullanici adi veya sifre hatali")


def main():
    app = QApplication([])
    login = LoginWindow()
    if login.exec() == QDialog.DialogCode.Accepted:
        window = MainWindow(login.user)
        window.show()
        app.exec()


if __name__ == "__main__":
    main()

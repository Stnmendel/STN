# AetherAI Demo

This repository contains a simple Flask web application demonstrating an AI assistant called **AetherAI**. The application includes a basic chat interface and a placeholder subscription check.

## Running the app

1. Install dependencies:
   ```bash
   pip install flask
   ```
2. Start the server:
   ```bash
   python app.py
   ```
3. Open `http://localhost:5000` in your browser.

A single demo user `demo@example.com` is subscribed by default. Integrate your own subscription and AI logic as needed.

## Running the POS demo

The repository also includes a small POS (Point of Sale) demo using PyQt6 and SQLAlchemy.
To run it:

```bash
pip install PyQt6 sqlalchemy python-barcode
python -m pos_app.main
```

The application creates an SQLite database `pos.db` in the project directory and
adds a default user (`Admin`/`1`). After logging in you can simulate sales by
entering product barcodes. F6 tuşu ile açılan Yönetici Paneli üzerinden ürünleri
yönetebilir ve python-barcode kurulmuşsa seçilen ürünün barkodunu
`static/barcodes` klasörüne kaydedebilirsiniz.

Müşteri hesaplarını yönetmek için Yönetici Panelinde bulunan **Müşteri İşlemleri** bölümünü kullanabilirsiniz. Buradan yeni müşteri ekleyebilir ve veresiye satış bakiyelerini takip edebilirsiniz.

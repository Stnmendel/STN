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

Finans işlemleri ve raporlamalar için **Finans ve Raporlar** menüsünü kullanın. Bu bölümde gider girişi yapabilir, müşterilerden tahsilat veya onlara yapılan ödemeleri kaydedebilir ve seçtiğiniz gün için özet kasa raporu alabilirsiniz.

Stok girişleri ve tedarikçi takibi için **Toptancı İşlemleri** bölümünü kullanabilirsiniz. Buradan tedarikçilerinizi ekleyebilir ve "Yeni Mal Alımı Yap" seçeneği ile ürün alış faturaları oluşturabilirsiniz. Alım tamamlandığında ürün stok miktarları ve alış fiyatları güncellenir, ilgili toptancının bakiyesi ise fatura tutarı kadar artırılır.

Personel yetkilerini yönetmek için **Personel İşlemleri** penceresini kullanın. Sadece `Admin` rolüne sahip kullanıcılar yönetici ekranlarına erişebilir ve genel ayarları güncelleyebilir. `Genel Ayarlar` menüsünde firma adı, adres gibi bilgileri düzenleyebilir ve F12 ile yazdırılan fişlerde kullanılmasını sağlayabilirsiniz.

Finans menüsündeki **Gelişmiş Raporlar** ekranı; seçilen tarih aralığında kâr/zarar analizi, ürün bazında kârlılık, en çok satan ürünler ve stok değeri gibi raporları sunar. Ayrıca **Yardımcı Araçlar** bölümünden veritabanını yedekleyebilir veya bir yedeği geri yükleyebilirsiniz.

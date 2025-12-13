# 🍽️ Django Food Ordering System

Sistem pemesanan makanan berbasis Django dengan multi-role: Admin,
Customer, Driver, dan Restaurant.

## 🖼️ Tampilan Dashboard (Preview)

> Ganti link gambar di bawah dengan gambar dari repo kamu

### **Dashboard Admin**

![Admin
Dashboard](https://raw.githubusercontent.com/username/repo/main/screenshots/admin_dashboard.png)

### **Dashboard Customer**

![Customer
Dashboard](https://raw.githubusercontent.com/username/repo/main/screenshots/customer_dashboard.png)

### **Dashboard Resto**

![Resto
Dashboard](https://raw.githubusercontent.com/username/repo/main/screenshots/resto_dashboard.png)

### **Dashboard Driver**

![Driver
Dashboard](https://raw.githubusercontent.com/username/repo/main/screenshots/driver_dashboard.png)

## 📌 Fitur Utama

### 🔐 **Admin**

-   Mengelola semua user\
-   Mengelola menu & restoran\
-   Mengontrol order dan driver

### 🍔 **Customer**

-   Pesan makanan\
-   Lihat status order\
-   Tracking driver

### 🛵 **Driver**

-   Terima order\
-   Update status pengantaran\
-   Lihat riwayat pengiriman

### 🍽️ **Restaurant**

-   Kelola menu\
-   Terima pesanan baru\
-   Update status makanan

## 📁 Struktur Proyek

Pbo/ │── manage.py │── requirements.txt │── README.md │ ├── accounts/
├── restaurants/ ├── drivers/ ├── orders/ ├── templates/ ├── static/ └──
venv/ (tidak diupload)

## 🚀 Cara Menjalankan Project

### **1. Clone Repo**

git clone https://github.com/EllNoStrong/Pbo.git cd Pbo

### **2. Buat Virtual Environment**

Windows: python -m venv venv venv`\Scripts`{=tex}`\activate`{=tex}

MacOS / Linux: python3 -m venv venv source venv/bin/activate

### **3. Install Dependencies**

pip install -r requirements.txt

### **4. Migrate Database**

python manage.py migrate

### **5. Jalankan Server**

python manage.py runserver

http://127.0.0.1:8000/

## 🔐 Akun Superuser (Admin Panel)

Username: adminpanel Password: admin123

## ❗ Catatan Penting

-   Jangan push venv/
-   Jangan push db.sqlite3
-   Update selalu requirements.txt dengan: pip freeze \>
    requirements.txt

## 👨‍💻 Developer

Marcellino Rafael\
Teknik Elektro -- Universitas Negeri Semarang

## 📞 Bantuan

Jika mengalami error, silakan kontak developer.

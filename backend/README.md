# CV-Matcher Backend API

FastAPI tabanlı CV ve İş İlanı Eşleştirme Sistemi backend'i.

## 🚀 Başlangıç

### Gereksinimler
- Python 3.10+
- PostgreSQL (Neon.tech cloud veya local)
- Hugging Face API Token

### Kurulum

1. **Sanal ortamı oluştur ve aktifleştir:**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **Bağımlılıkları yükle:**
```bash
pip install -r requirements.txt
```

3. **Environment değişkenlerini ayarla:**
```bash
cp .env.example .env
# .env dosyasını kendi bilgilerinle doldur
```

4. **Uvicorn ile çalıştır:**
```bash
python -m uvicorn app.main:app --reload
```

API şu adreste açılacak: http://localhost:8000

## 📊 Veritabanını Örnek Veriler ile Doldurmak

### Seçenek 1: CLI Script'i ile (Önerilir - Local Development)

```bash
python seed.py
```

**Çıktı:**
```
--- VERİTABANI TOHUMLAMA BAŞLADI ---
Sistem işveren kullanıcısı bulunamadı, oluşturuluyor...
İlanlar şu kullanıcıya bağlanacak: ID 2 (Sistem İşe Alım Departmanı)
1000 adet ilan hazırlanıyor...
✔ 1000 adet karışık iş ilanı başarıyla veritabanına yüklendi!
--- İŞLEM BİTTİ ---
```

### Seçenek 2: HTTP API Endpoint'i ile (Production/Test)

**Render veya Vercel'de deployment sonrası:**

```bash
curl -X POST "http://localhost:8000/admin/seed-database?admin_key=your-admin-key"
```

veya

```bash
curl -X POST "https://your-render-url.com/api/v1/admin/seed-database?admin_key=YOUR_ADMIN_SEED_KEY"
```

**Başarılı Yanıt:**
```json
{
  "message": "Veritabanı tohumlama başarıyla tamamlandı!"
}
```

## 📝 Seed Script Detayları

`seed.py` scripti şunları yapar:

1. **Sistem İşveren Kullanıcısını Oluşturur**
   - Email: `sistem@isveren.com`
   - Tüm ilanların sahibi olur

2. **1000 Adet Örnek İş İlanı Oluşturur**
   - 10 farklı sektörden
   - Rastgele pozisyon, şirket, konum
   - Gerçekçi maaş aralıkları
   - Çeşitli çalışma türleri (remote, hybrid, office)
   - Deneyim seviyeleri (entry, mid, senior)

3. **Veritabanını Toplu Ekleme ile Doldurur**
   - Performans: ~5-10 saniye
   - Çifte tohumlama kontrolü ile koruma

## 🔑 Önemli Notlar

### Environment Variables

| Değişken | Açıklama | Örnek |
|----------|----------|--------|
| `DATABASE_URL` | PostgreSQL bağlantı stringi | `postgresql://user:pass@host/db` |
| `HF_TOKEN` | Hugging Face API Token | `hf_xyzabc...` |
| `JWT_SECRET_KEY` | JWT imzalama anahtarı | `your-secret` |
| `ADMIN_SEED_KEY` | Seed endpoint'i koruma anahtarı | `super-secret-admin-key` |

### Seed Script Çalıştırma Koşulları

- ✅ Veritabanı boş veya zaten seed'lenmiş olmalı
- ✅ Sistem işveren kullanıcısı otomatik oluşturulur
- ❌ Aynı owner'a ait ilanlar zaten varsa skip edilir (koruma mekanizması)

## 🏗️ Proje Yapısı

```
backend/
├── app/
│   ├── api/endpoints/          # Route handlers
│   ├── core/                   # Database, security, config
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   ├── services/               # Business logic (matching, analysis)
│   └── main.py                 # FastAPI app
├── seed.py                     # Veritabanı tohumlama scripti
├── requirements.txt            # Python dependencies
└── .env                        # Environment variables (git ignore)
```

## 🧪 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Kullanıcı kayıt
- `POST /api/v1/auth/login` - Kullanıcı giriş

### CV Management
- `POST /api/v1/cv/upload-and-analyze` - CV yükle ve analiz et
- `GET /api/v1/cv/my-cvs` - Kendi CV'leri listele
- `DELETE /api/v1/cv/{cv_id}` - CV sil

### Job Management
- `GET /api/v1/jobs` - İş ilanlarını listele
- `POST /api/v1/jobs` - İş ilanı oluştur
- `PUT /api/v1/jobs/{job_id}` - İş ilanı güncelle

### Matching
- `POST /api/v1/match-jobs` - İş ilanlarıyla eşleştir
- `POST /api/v1/matches/{job_id}/{resume_id}` - Detaylı eşleştirme analizi

## 🔧 Teknoloji Stack

- **Framework**: FastAPI 0.115+
- **Database ORM**: SQLAlchemy 2.0
- **Database**: PostgreSQL (Neon.tech)
- **Auth**: JWT + OAuth
- **AI/ML**: Hugging Face Inference API
- **NLP**: NLTK
- **Embedded Models**: Sentence Transformers (via HF API)

## ⚙️ Performance Optimizations

- ✅ HF API kullanarak local model yüklemeyi elimine ettik (RAM < 100MB)
- ✅ Lazy loading ve thread-safe implementasyon
- ✅ Bulk insert ile toplu ekleme
- ✅ Database query optimization
- ✅ CORS dynamic origins

## 📖 Daha Fazla Bilgi

- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Ana Proje README: `../../README.md`

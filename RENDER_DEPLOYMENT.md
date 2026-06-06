# Render Deployment Guide

## ✅ Seçilen: Python Runtime (Recommended)

### Render Dashboard Ayarları:

1. **New > Web Service** tıklayın
2. GitHub repository'i bağlayın: `https://github.com/iberil/ai-cv-matcher`
3. **Build & Deploy** sekmesinde:

#### Service Settings:
- **Name**: `cv-matcher-api`
- **Region**: `Frankfurt` (EU Central)
- **Runtime**: `Python 3.11`
- **Build Command**: 
  ```
  pip install -r backend/requirements.txt
  ```
- **Start Command**:
  ```
  gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.app.main:app --bind 0.0.0.0:10000
  ```

#### Environment Variables:
```
DATABASE_URL=postgresql://neondb_owner:password@ep-cool-lake-a2.eu-central-1.aws.neon.tech/neondb?sslmode=require
JWT_SECRET_KEY=your-secret-key
HF_TOKEN=your-huggingface-token
PYTHONUNBUFFERED=true
```

### Root Directory:
```
./
```

### Logs:
Deployment'dan sonra `/docs` adresinde API'nin çalıştığını görebilirsin:
```
https://cv-matcher-api.onrender.com/docs
```

### Deploy Sonrası:
1. Neon'dan database migrations çalıştır
2. Test et: `curl https://cv-matcher-api.onrender.com/health`
3. Frontend'de `.env.local` dosyasını güncelle:
   ```
   NEXT_PUBLIC_API_URL=https://cv-matcher-api.onrender.com/api/v1
   ```

## 🚀 Deployment Başarılı Olduğunu Nasıl Anlarız:
- ✅ Build tamamlandı
- ✅ Logs'ta hata yok
- ✅ `/health` endpoint 200 döndürüyor
- ✅ `/docs` Swagger UI açılıyor

## ⚠️ Sorun Yaşarsan:
- Logs kısmında hataları kontrol et
- `DEBUG=False` olduğundan emin ol
- Neon database connection string'ini verify et
- Timeout issues için build & start command'leri kontrol et

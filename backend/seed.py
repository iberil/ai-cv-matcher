# -*- coding: utf-8 -*-
import os
import sys
import random
from sqlalchemy.orm import Session

# Backend app'ı import etmek için path'i ayarla
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine
from app.models import User
from app.models.job_posting import JobPosting
from app.core.security import get_password_hash

# Sektör ve Pozisyon Havuzu
sektor_verileri = {
    "Tarım ve Hayvancılık": {
        "pozisyonlar": ["Ziraat Mühendisi", "Akıllı Tarım Uzmanı", "Sulama Sistemleri Teknisyeni", "Tedarik Zinciri Sorumlusu", "Dikey Tarım Operatörü"],
        "beceriler": "IoT, Sensör Teknolojileri, Drone Kullanımı, Excel, Veri Analizi"
    },
    "Lojistik ve Taşımacılık": {
        "pozisyonlar": ["Operasyon Yöneticisi", "Gümrük Müşavir Yardımcısı", "Filo Koordinatörü", "Depo Yönetim Uzmanı", "Uluslararası Nakliye Sorumlusu"],
        "beceriler": "SAP, ERP, Excel, İngilizce, Planlama, Stok Yönetimi"
    },
    "Eğitim ve Danışmanlık": {
        "pozisyonlar": ["Eğitim Teknoloğu", "İngilizce Öğretmeni", "Akademik Danışman", "Kurumsal Eğitmen", "Öğrenci İşleri Uzmanı"],
        "beceriler": "Sunum Becerileri, LMS, Zoom/Teams, Pedagojik Formasyon, İngilizce"
    },
    "Gıda ve Restoran": {
        "pozisyonlar": ["Gıda Mühendisi", "Restoran Müdürü", "Mutfak Şefi", "Kalite Kontrol Sorumlusu", "Diyetisyen"],
        "beceriler": "HACCP, ISO 22000, Hijyen Eğitimi, Ekip Yönetimi, Maliyet Analizi"
    },
    "İnşaat ve Emlak": {
        "pozisyonlar": ["Şantiye Şefi", "İnşaat Mühendisi", "Gayrimenkul Danışmanı", "BIM Uzmanı", "Mimar"],
        "beceriler": "AutoCAD, Revit, MS Project, Statik Analiz, Saha Yönetimi"
    },
    "Tekstil ve Moda": {
        "pozisyonlar": ["Modelist", "Tekstil Mühendisi", "Moda Tasarımcısı", "Planlama Uzmanı", "Satın Alma Sorumlusu"],
        "beceriler": "Adobe Illustrator, Gerber, Örme Bilgisi, Kumaş Analizi, PLM"
    },
    "Hukuk ve Uyum": {
        "pozisyonlar": ["Avukat", "Hukuk Müşaviri", "KVKK Danışmanı", "Uyum (Compliance) Uzmanı", "İcra Katibi"],
        "beceriler": "KVKK, GDPR, UYAP, Ticaret Hukuku, Sözleşme Yönetimi"
    },
    "Medya ve Sanat": {
        "pozisyonlar": ["Video Editor", "Grafik Tasarımcı", "İçerik Editörü", "Sosyal Medya Yöneticisi", "Kreatif Direktör"],
        "beceriler": "Adobe Premiere, After Effects, Photoshop, SEO, Metin Yazarlığı"
    },
    "Sağlık ve İlaç": {
        "pozisyonlar": ["Tıbbi Mümessil", "Biyomedikal Mühendisi", "Hasta Kabul Sorumlusu", "Laboratuvar Teknisyeni", "Eczacı"],
        "beceriler": "İlaç Tanıtımı, Tıbbi Cihaz Bakımı, Excel, İletişim, Raporlama"
    },
    "Turizm ve Otelcilik": {
        "pozisyonlar": ["Ön Büro Müdürü", "Tur Operatörü", "Kat Hizmetleri Sorumlusu", "Acente Satış Temsilcisi", "Etkinlik Planlamacı"],
        "beceriler": "Opera, Amadeus, İngilizce, Rusça, CRM, Satış Teknikleri"
    }
}

sirketler = ["Anadolu", "Yıldız", "Global", "Mavi", "Yeşil", "Zirve", "Merkez", "Modern", "Özgün", "Birlik"]
ekler = ["A.Ş.", "Grup", "Holding", "Limited", "Hizmetleri", "Ticaret"]
konumlar = ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Adana", "Gaziantep", "Kayseri"]
calisma_turleri = ["remote", "hybrid", "office"]
deneyim_seviyeleri = ["entry", "mid", "senior"]

def seed_database():
    db: Session = SessionLocal()
    try:
        print("--- VERITABANI TOHUMLAMA BASLADI ---")
        
        # 1. Sistem işveren kullanıcısını kontrol et/oluştur
        system_employer = db.query(User).filter(User.email == "sistem@isveren.com").first()
        if not system_employer:
            print("Sistem isveren kullanicisi bulunamadi, olusturuluyor...")
            system_employer = User(
                full_name="Sistem Ise Alim Departmani",
                email="sistem@isveren.com",
                hashed_password=get_password_hash("SistemSifresi123!"),
                user_role="isveren",
                is_active=True
            )
            db.add(system_employer)
            db.flush()
        
        creator_id = system_employer.id
        print(f"Ilanlar su kullaniciya baglanacak: ID {creator_id} ({system_employer.full_name})")

        # 2. Mevcut ilanları kontrol et (çifte tohumlama önleme)
        existing_count = db.query(JobPosting).filter(JobPosting.created_by == creator_id).count()
        if existing_count > 0:
            print(f"UYARI: Zaten {existing_count} adet ilan mevcut. Toplu ekleme yapmiyorum.")
            print("Devam etmek istiyorsaniz var olan ilanlar silin veya baska bir creator_id kullanin.")
            return

        # 3. 1000 adet ilan üret
        job_postings_to_add = []
        for i in range(1000):
            sektor_adi = random.choice(list(sektor_verileri.keys()))
            detay = sektor_verileri[sektor_adi]
            
            pozisyon = random.choice(detay["pozisyonlar"])
            sirket = f"{random.choice(sirketler)} {random.choice(sirketler)} {random.choice(ekler)}"
            
            konum = random.choice(konumlar)
            work_type = random.choice(calisma_turleri)
            if work_type == "remote":
                konum = "Uzaktan - Turkiye"

            min_maas = random.randrange(35000, 85000, 2500)
            max_maas = min_maas + random.randrange(10000, 40000, 5000)
            
            aciklama = f"{sektor_adi} alaninda buyuyen ekibimize {pozisyon} olarak katkis saglaycak, sorumluluk sahibi takim arkadaslari ariyoruz."
            gereksinim = f"Ilgili universite bolumlerinden mezun, sektorde tecrubesi olan ve dinamik calisma ortamina uyum saglyabilecek adaylar."
            exp_level = random.choice(deneyim_seviyeleri)

            new_job = JobPosting(
                title=pozisyon,
                company_name=sirket,
                location=konum,
                description=aciklama,
                requirements=gereksinim,
                skills_required=detay["beceriler"],
                work_type=work_type,
                experience_level=exp_level,
                salary_min=float(min_maas),
                salary_max=float(max_maas),
                sector=sektor_adi,
                is_active=True,
                created_by=creator_id
            )
            job_postings_to_add.append(new_job)

        # 4. Toplu ekleme
        print(f"{len(job_postings_to_add)} adet ilan hazirlaniyor...")
        db.bulk_save_objects(job_postings_to_add)
        db.commit()
        print("[SUCCESS] 1000 adet karisik is ilani basariyila veritabanina yuklendi!")
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Tohumlama sirasinda bir hata olustu: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        print("--- ISLEM BITTI ---")

if __name__ == "__main__":
    seed_database()

import os
import sys
import random
from sqlalchemy.orm import Session

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
        print("--- VERİTABANI TOHUMLAMA BAŞLADI ---")
        
        # 1. Sistem işveren kullanıcısını kontrol et/oluştur
        system_employer = db.query(User).filter(User.email == "sistem@isveren.com").first()
        if not system_employer:
            print("Sistem işveren kullanıcısı bulunamadı, oluşturuluyor...")
            system_employer = User(
                full_name="Sistem İşe Alım Departmanı",
                email="sistem@isveren.com",
                hashed_password=get_password_hash("SistemSifresi123!"),
                user_role="isveren",
                is_active=True
            )
            db.add(system_employer)
            db.flush()
        
        owner_id = system_employer.id
        print(f"İlanlar şu kullanıcıya bağlanacak: ID {owner_id} ({system_employer.full_name})")

        # 2. Mevcut ilanları kontrol et (çifte tohumlama önleme)
        existing_count = db.query(JobPosting).filter(JobPosting.owner_id == owner_id).count()
        if existing_count > 0:
            print(f"⚠️  Zaten {existing_count} adet ilan mevcut. Toplu ekleme yapmıyorum.")
            print("Devam etmek istiyorsanız var olan ilanları silin veya başka bir owner_id kullanın.")
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
                konum = "Uzaktan - Türkiye"

            min_maas = random.randrange(35000, 85000, 2500)
            max_maas = min_maas + random.randrange(10000, 40000, 5000)
            
            aciklama = f"{sektor_adi} alanında büyüyen ekibimize {pozisyon} olarak katkı sağlayacak, sorumluluk sahibi takım arkadaşları arıyoruz."
            gereksinim = f"İlgili üniversite bölümlerinden mezun, sektörde tecrübesi olan ve dinamik çalışma ortamına uyum sağlayabilecek adaylar."
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
                owner_id=owner_id
            )
            job_postings_to_add.append(new_job)

        # 4. Toplu ekleme
        print(f"{len(job_postings_to_add)} adet ilan hazırlanıyor...")
        db.bulk_save_objects(job_postings_to_add)
        db.commit()
        print("✔ 1000 adet karışık iş ilanı başarıyla veritabanına yüklendi!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Tohumlama sırasında bir hata oluştu: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        print("--- İŞLEM BİTTİ ---")

if __name__ == "__main__":
    seed_database()

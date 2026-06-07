# -*- coding: utf-8 -*-
import os
import sys
import random
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine
from app.models import User
from app.models.job_posting import JobPosting, CVJobMatch
from app.core.security import get_password_hash

# GERÇEKÇİ VE KATEGORİZE EDİLMİŞ VERİ HAVUZU
job_market_data = [
    {
        "sector": "Bilgi Teknolojileri ve Yazılım",
        "companies": ["Trendyol", "Getir", "OBSS", "Softtech", "Enoca", "DefineX", "Aselsan", "Havelsan", "Turkcell", "Vodafone", "Kariyer.net", "Sahibinden", "Commencis", "Etiya"],
        "roles": [
            {"title": "Backend Developer", "skills": "Java, Spring Boot, Python, FastAPI, C#, .NET Core, Microservices, PostgreSQL, Redis"},
            {"title": "Frontend Developer", "skills": "JavaScript, TypeScript, React, Next.js, Angular, Vue.js, HTML5, CSS3, Tailwind"},
            {"title": "Full Stack Developer", "skills": "JavaScript, React, Node.js, Python, MongoDB, SQL, Git, REST API"},
            {"title": "Data Engineer", "skills": "Python, SQL, Apache Spark, Hadoop, Airflow, ETL, BigQuery, AWS, Kafka"},
            {"title": "Data Scientist", "skills": "Python, Machine Learning, Deep Learning, TensorFlow, PyTorch, Scikit-learn, SQL, Pandas"},
            {"title": "DevOps Engineer", "skills": "Linux, Docker, Kubernetes, CI/CD, Jenkins, Terraform, AWS, Azure, Bash"},
            {"title": "iOS Developer", "skills": "Swift, iOS SDK, Xcode, CoreData, RESTful APIs, Git"},
            {"title": "Android Developer", "skills": "Kotlin, Android Studio, Java, MVVM, Coroutines, REST API"},
            {"title": "QA Automation Engineer", "skills": "Selenium, Cypress, Appium, Python, Java, Test Automation, Postman"},
            {"title": "AI/ML Engineer", "skills": "Python, PyTorch, NLP, LLM, Hugging Face, Computer Vision, MLOps"},
            {"title": "Cyber Security Analyst", "skills": "Network Security, CEH, Penetration Testing, SIEM, Linux, Cryptography"},
            {"title": "Product Owner", "skills": "Agile, Scrum, Jira, Product Management, UX/UI, Wireframing"}
        ]
    },
    {
        "sector": "Finans ve Bankacılık",
        "companies": ["Garanti BBVA", "Akbank", "İş Bankası", "Yapı Kredi", "QNB Finansbank", "DenizBank", "Allianz", "Anadolu Sigorta"],
        "roles": [
            {"title": "İş Analisti", "skills": "SQL, Excel, BPMN, Gereksinim Analizi, Agile, Jira, Veri Modelleme"},
            {"title": "Veri Analisti", "skills": "SQL, Python, Power BI, Tableau, Excel, İstatistik, Raporlama"},
            {"title": "Risk Yönetimi Uzmanı", "skills": "Finansal Analiz, Risk Modelleme, Python, Basel, Kredi Riski"},
            {"title": "Mali Müşavir / Muhasebe", "skills": "Logo, SAP FI, Vergi Mevzuatı, Bilanço, Mutabakat"}
        ]
    },
    {
        "sector": "E-Ticaret ve Perakende",
        "companies": ["Migros", "CarrefourSA", "BİM", "A101", "LC Waikiki", "Boyner", "DeFacto", "Koton"],
        "roles": [
            {"title": "E-Ticaret Yöneticisi", "skills": "Dijital Pazarlama, SEO, Google Analytics, Shopify, E-ihracat"},
            {"title": "Tedarik Zinciri Uzmanı", "skills": "Lojistik, ERP, SAP, Stok Yönetimi, Planlama, Excel"},
            {"title": "Kategori Uzmanı", "skills": "Fiyatlandırma, Rakip Analizi, Satış Stratejisi, Excel, İletişim"}
        ]
    },
    {
        "sector": "Sağlık ve İlaç",
        "companies": ["Acıbadem", "Memorial", "Florence Nightingale", "Abdi İbrahim", "Deva Holding", "Nobel İlaç"],
        "roles": [
            {"title": "Biyomedikal Mühendisi", "skills": "Tıbbi Cihazlar, ISO 13485, Kalibrasyon, Bakım Onarım, Teknik Destek"},
            {"title": "Klinik Araştırma Uzmanı", "skills": "GCP, Klinik Çalışmalar, Dokümantasyon, İngilizce, Raporlama"},
            {"title": "Sağlık Veri Analisti", "skills": "SQL, Sağlık Bilişimi, Python, Veri Madenciliği, İstatistik"}
        ]
    },
    {
        "sector": "Otomotiv ve Üretim",
        "companies": ["Ford Otosan", "Tofaş", "Otokar", "BMC", "Mercedes-Benz Türk", "Bosch", "Toyota Türkiye"],
        "roles": [
            {"title": "Gömülü Sistemler Mühendisi (Embedded)", "skills": "C, C++, Microcontrollers, RTOS, ARM, CAN bus, MATLAB"},
            {"title": "Makine Mühendisi", "skills": "SolidWorks, AutoCAD, ANSYS, Üretim Planlama, Termodinamik"},
            {"title": "Kalite Güvence Mühendisi", "skills": "ISO 9001, Six Sigma, Lean Manufacturing, FMEA, Kalite Kontrol"},
            {"title": "Otomasyon Mühendisi", "skills": "PLC, SCADA, Siemens, TIA Portal, Robotik, HMI"}
        ]
    },
    {
        "sector": "Telekomünikasyon",
        "companies": ["Turkcell", "Vodafone", "Türk Telekom", "Netaş"],
        "roles": [
            {"title": "Network Mühendisi", "skills": "Cisco, CCNA, BGP, OSPF, TCP/IP, Firewall, Routing & Switching"},
            {"title": "Telekomünikasyon Uzmanı", "skills": "5G, LTE, Fiber Optik, RF Planlama, Transmisyon"},
            {"title": "Sistem Yöneticisi", "skills": "Linux, Windows Server, VMware, Active Directory, Backup"}
        ]
    }
]

konumlar = ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Kocaeli", "Eskişehir", "Gaziantep", "Uzaktan"]
calisma_turleri = ["remote", "hybrid", "office"]
deneyim_seviyeleri = ["entry", "mid", "senior"]

def generate_description(sector, title, company):
    desc_templates = [
        f"{company} olarak, {sector} sektöründeki yenilikçi projelerimizde görev alacak deneyimli bir {title} arıyoruz.",
        f"Büyüyen ekibimize katılmak üzere, tutkulu ve teknolojiye meraklı bir {title} arayışımız bulunmaktadır.",
        f"Kariyerinizi {company} çatısı altında, alanında uzman ekiplerle çalışarak ileriye taşımak isterseniz bu ilan tam size göre!",
        f"{sector} alanında pazar lideri olan şirketimizde, {title} pozisyonunda fark yaratacak takım arkadaşları arıyoruz."
    ]
    return random.choice(desc_templates)

def seed_database():
    db: Session = SessionLocal()
    try:
        print("--- VERİTABANI TOHUMLAMA BAŞLADI ---")
        
        system_employer = db.query(User).filter(User.email == "sistem@isveren.com").first()
        if not system_employer:
            print("Sistem işveren kullanıcısı oluşturuluyor...")
            system_employer = User(
                full_name="Sistem İşe Alım Departmanı",
                email="sistem@isveren.com",
                hashed_password=get_password_hash("SistemSifresi123!"),
                user_role="isveren",
                is_active=True
            )
            db.add(system_employer)
            db.flush()
        
        creator_id = system_employer.id

        # ESKİ İLANLARI TEMİZLE
        existing_jobs = db.query(JobPosting).filter(JobPosting.created_by == creator_id)
        existing_count = existing_jobs.count()
        if existing_count > 0:
            print(f"Mevcut {existing_count} ilan ve ilişkili eşleşmeler siliniyor...")
            job_ids = [job.id for job in existing_jobs.all()]
            if job_ids:
                db.query(CVJobMatch).filter(CVJobMatch.job_posting_id.in_(job_ids)).delete(synchronize_session=False)
            existing_jobs.delete(synchronize_session=False)
            db.commit()

        # 1200 YENİ VE GERÇEKÇİ İLAN ÜRET
        job_postings_to_add = []
        for _ in range(1200):
            # 1. Sektörü seç (Bilişim sektörünün gelme ihtimalini artırmak için ağırlıklı seçim yapılabilir, ama şimdilik rastgele)
            market = random.choice(job_market_data)
            sector_name = market["sector"]
            
            # 2. Sektörün içinden uygun bir şirket ve rol seç
            company = random.choice(market["companies"])
            role = random.choice(market["roles"])
            
            pozisyon = role["title"]
            beceriler = role["skills"]
            
            # 3. Çalışma türü ve konum mantığı (IT işleri daha çok remote/hybrid olur)
            work_type = random.choice(calisma_turleri)
            if work_type == "remote" or sector_name == "Bilgi Teknolojileri ve Yazılım" and random.random() > 0.5:
                konum = "Uzaktan (Tüm Türkiye)"
                work_type = "remote" if work_type == "office" else work_type
            else:
                konum = random.choice(konumlar)

            # 4. Maaş mantığı (Senior daha çok alır, IT daha çok alır vb.)
            exp_level = random.choice(deneyim_seviyeleri)
            base_salary = 40000 if exp_level == "entry" else (70000 if exp_level == "mid" else 110000)
            if sector_name == "Bilgi Teknolojileri ve Yazılım":
                base_salary += 20000
                
            min_maas = base_salary + random.randrange(-5000, 15000, 2500)
            max_maas = min_maas + random.randrange(15000, 50000, 5000)
            
            aciklama = generate_description(sector_name, pozisyon, company)
            gereksinim = f"İlgili bölümlerden mezun, {exp_level} seviyesinde tecrübeye sahip, belirtilen teknoloji ve yetkinliklerde uzman adaylar."

            new_job = JobPosting(
                title=pozisyon,
                company_name=company,
                location=konum,
                description=aciklama,
                requirements=gereksinim,
                skills_required=beceriler,
                work_type=work_type,
                experience_level=exp_level,
                salary_min=float(min_maas),
                salary_max=float(max_maas),
                sector=sector_name,
                is_active=True,
                created_by=creator_id
            )
            job_postings_to_add.append(new_job)

        print(f"Toplam {len(job_postings_to_add)} yeni nesil, mantıklı ilan hazırlanıyor...")
        db.bulk_save_objects(job_postings_to_add)
        db.commit()
        print("[SUCCESS] İlanlar başarıyla Neon.tech veritabanına yüklendi!")
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Tohumlama sırasında bir hata oluştu: {e}")
    finally:
        db.close()
        print("--- İŞLEM BİTTİ ---")

if __name__ == "__main__":
    seed_database()
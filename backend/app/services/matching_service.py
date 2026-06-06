
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import logging
import os
import threading

# Tokenizer hata vermemesi için Windows/Multithread ortamı paralellik ayarı
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Global Model Lock
_model_lock = threading.Lock()

# NLTK verilerini indir (ilk çalıştırmada)
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

from ..core.matching_constants import (
    CRITICAL_SKILLS, TECH_JOB_KEYWORDS, 
    NON_TECH_EDUCATION_KEYWORDS, TECH_EDUCATION_KEYWORDS
)

class CVJobMatcher:
    def __init__(self):
        self.model = None
        self.stop_words = set(stopwords.words('english'))
        
    def _load_model(self):
        """Model'i lazy loading ile yükle (Thread-Safe)"""
        if self.model is None:
            with _model_lock:
                if self.model is None:
                    # Türkçe destekleyen küçük ve hızlı model
                    self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2') 
        return self.model
        
    def preprocess_text(self, text: str) -> str:
        """Metni temizle ve normalize et"""
        if not text:
            return ""
        
        # Küçük harfe çevir
        text = text.lower()
        
        # Özel karakterleri temizle
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Fazla boşlukları temizle
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_skills_and_keywords(self, text: str) -> List[str]:
        """Metinden beceri ve anahtar kelimeleri çıkar"""
        processed_text = self.preprocess_text(text)
        
        # Tokenize et
        tokens = word_tokenize(processed_text)
        
        # Stop words'leri filtrele ve minimum uzunluk kontrolü
        keywords = [token for token in tokens 
                   if token not in self.stop_words and len(token) > 2]
        
        return keywords
    
    def create_cv_profile(self, cv_data: Dict) -> str:
        """CV verilerinden profil metni oluştur"""
        profile_parts = []
        if cv_data.get('skills'):
            profile_parts.append(f"Skills: {cv_data['skills']}")
        if cv_data.get('experience'):
            profile_parts.append(f"Experience: {cv_data['experience']}")
        if cv_data.get('education'):
            profile_parts.append(f"Education: {cv_data['education']}")
        if cv_data.get('summary'):
            profile_parts.append(f"Summary: {cv_data['summary']}")
        return " ".join(profile_parts)
    
    def create_job_profile(self, job_data: Dict) -> str:
        """İş ilanı verilerinden profil metni oluştur"""
        profile_parts = []
        if job_data.get('title'):
            profile_parts.append(f"Job Title: {job_data['title']}")
        if job_data.get('description'):
            profile_parts.append(f"Description: {job_data['description']}")
        if job_data.get('requirements'):
            profile_parts.append(f"Requirements: {job_data['requirements']}")
        if job_data.get('skills_required'):
            profile_parts.append(f"Required Skills: {job_data['skills_required']}")
        return " ".join(profile_parts)
    
    def calculate_similarity_score(self, cv_profile: str, job_profile: str) -> float:
        """İki profil arasındaki benzerlik skorunu hesapla"""
        try:
            # Model'i lazy loading ile yükle
            model = self._load_model()
            
            # Metinleri embedding'e çevir
            cv_embedding = model.encode([cv_profile])
            job_embedding = model.encode([job_profile])
            
            # Cosine similarity hesapla
            similarity = cosine_similarity(cv_embedding, job_embedding)[0][0]
            
            # 0-100 arası skora çevir
            return float(similarity * 100)
            
        except Exception as e:
            logging.error(f"Similarity calculation error: {e}")
            return 0.0
    
    def calculate_critical_skill_penalty(self, cv_data: Dict, job_data: Dict) -> float:
        """
        Kritik beceri uyumsuzluğu için VETO sistemi ile ceza hesapla.
        """
        
        # 1. EĞİTİM GEREKSİNİMİ KONTROLÜ (EN ÖNCELİKLİ)
        education_penalty = self._check_education_requirement(cv_data, job_data)
        if education_penalty <= -50:
            logging.info(f"EDUCATION VETO: Penalty = {education_penalty}")
            return education_penalty
        
        # 2. KRİTİK BECERİ KONTROLÜ
        
        # Verileri hazırla
        cv_skills_text = f"{cv_data.get('skills', '')} {cv_data.get('experience', '')} {cv_data.get('summary', '')}".lower()
        job_profile_text = f"{job_data.get('title', '')} {job_data.get('description', '')} {job_data.get('requirements', '')} {job_data.get('skills_required', '')}".lower()
        
        # CV teknoloji odaklı mı?
        tech_keywords = ['developer', 'engineer', 'programmer', 'software', 'code', 'programming', 'mühendis', 'geliştirici', 'yazılım']
        is_tech_cv = any(keyword in cv_skills_text for keyword in tech_keywords)
        
        # KRİTİK BECERİ EŞLEŞTİRME - VETO SİSTEMİ
        matched_role = None
        matched_config = None
        
        # CRITICAL_SKILLS zaten spesifikten genele doğru sıralıdır (constants.py)
        # Bu yüzden sırayla kontrol etmek yeterlidir.
        for role, config in CRITICAL_SKILLS.items():
            role_in_job = any(keyword in job_profile_text for keyword in config['keywords'])
            if role_in_job:
                matched_role = role
                matched_config = config
                break
        
        # Eşleşen rol varsa kontrol et
        if matched_role and matched_config:
            logging.info(f"DEBUG - '{matched_role}' rolü iş ilanında tespit edildi.")
            
            # Eğer gerekli beceri listesi boşsa (Avukat, Doktor vb.), direkt ceza veya geçiş
            if not matched_config['required']:
                # Eğer iş 'Avukat' gibi non-tech bir işse ve CV 'Developer' ise uyumsuzdur
                # Ancak 'Non-Tech' kategorisi (muhasebe vb.) için bu kuralı esnetebiliriz
                if matched_role not in ['Non-Tech'] and is_tech_cv:
                     # Örn: Avukat ilanına Developer başvurursa
                    logging.info(f"VETO: Teknoloji CV'si, '{matched_role}' rolü ile uyumsuz.")
                    return -100
                return 0.0
            
            # Aday bu kritik becerilerden KAÇ TANESİNE sahip?
            matched_skills = [skill for skill in matched_config['required'] if skill in cv_skills_text]
            matched_count = len(matched_skills)
            
            # DEBUG: Eşleşmeleri logla
            logging.info(f"DEBUG - Aranan: {matched_config['required'][:5]}...")
            logging.info(f"DEBUG - Bulunan: {matched_skills}")
            logging.info(f"DEBUG - Eşleşme Sayısı: {matched_count}")
            
            # Eğer hiçbir kritik beceri yoksa -> VETO
            if matched_count == 0:
                logging.info(f"VETO: İş ilanı '{matched_role}' rolünü istiyor ancak CV'de hiçbir kritik beceri bulunamadı.")
                return matched_config['penalty']
            else:
                logging.info(f"GEÇTİ: {matched_count} kritik beceri bulundu, '{matched_role}' için ceza yok.")
                return 0.0
        
        return 0.0  # Hiçbir kritere takılmazsa ceza yok
    
    def _check_education_requirement(self, cv_data: Dict, job_data: Dict) -> float:
        """
        Eğitim gereksinimi kontrolü - VETO sistemi
        Political Science mezunu teknik işlere başvuramaz
        """
        
        # CV eğitim bilgisi
        cv_education = cv_data.get('education', '').lower()
        
        # İş ilanı metni
        job_text = f"{job_data.get('title', '')} {job_data.get('description', '')} {job_data.get('requirements', '')}".lower()
        
        logging.info(f"EDUCATION CHECK - CV: {cv_education[:50]}...")
        logging.info(f"EDUCATION CHECK - Job: {job_text[:50]}...")
        
        # TEKNİK İŞLER İÇİN SIKI KONTROL
        # TECH_JOB_KEYWORDS constants dosyasından alınır
        
        # İş ilanı teknik mi?
        is_tech_job = any(keyword in job_text for keyword in TECH_JOB_KEYWORDS)
        logging.info(f"EDUCATION CHECK - Is tech job: {is_tech_job}")
        
        if is_tech_job:
            # 1. Önce Teknik Eğitimi Kontrol Et (Varsa Geçir)
            # TECH_EDUCATION_KEYWORDS constants dosyasından alınır
            has_tech_education = any(keyword in cv_education for keyword in TECH_EDUCATION_KEYWORDS)
            logging.info(f"EDUCATION CHECK - Has tech education: {has_tech_education}")
            
            if has_tech_education:
                logging.info(f"EDUCATION PASS: Teknik iş ilanı ve teknik eğitim mevcut.")
                return 0.0

            # 2. Teknik eğitimi yoksa, Teknik Olmayan (Veto) listesine bak
            # NON_TECH_EDUCATION_KEYWORDS constants dosyasından alınır
            has_non_tech_education = any(keyword in cv_education for keyword in NON_TECH_EDUCATION_KEYWORDS)
            logging.info(f"EDUCATION CHECK - Has non-tech education: {has_non_tech_education}")
            
            if has_non_tech_education:
                logging.info(f"EDUCATION VETO: Teknik iş ilanı, uyumsuz eğitim alanı - CV: {cv_education}")
                return -100  # Kesin uyumsuzluk
            
            # 3. Ne teknik ne de non-tech bulabildik (Belirsiz durum)
            logging.info(f"EDUCATION WARNING: Teknik iş ilanı, eğitim alanı belirsiz - CV: {cv_education}")
            return -90   # Yüksek ceza
        
        return 0.0  # Eğitim uyumlu
    
    def calculate_skill_match_bonus(self, cv_skills: List[str], job_skills: List[str]) -> float:
        """Beceri eşleşme bonusu hesapla"""
        if not cv_skills or not job_skills:
            return 0.0
        
        # Becerileri normalize et
        cv_skills_norm = [skill.lower().strip() for skill in cv_skills]
        job_skills_norm = [skill.lower().strip() for skill in job_skills]
        
        # Eşleşen beceri sayısı
        matches = len(set(cv_skills_norm) & set(job_skills_norm))
        
        # Bonus skoru (maksimum %20)
        bonus = min((matches / len(job_skills_norm)) * 20, 20)
        
        return bonus
    
    def calculate_skill_match_ratio(self, cv_data: Dict, job_data: Dict) -> float:
        """Beceri eşleşme oranını hesapla (0.0 - 1.0)"""
        cv_skills_text = f"{cv_data.get('skills', '')} {cv_data.get('experience', '')}".lower()
        job_skills_text = job_data.get('skills_required', '').lower()
        
        if not job_skills_text:
            return 0.5  # Beceri belirtilmemişse nötr
        
        # Becerileri parse et
        job_skills = [s.strip() for s in job_skills_text.split(',') if s.strip()]
        
        if not job_skills:
            return 0.5
        
        # Eşleşen beceri sayısı
        matched_count = sum(1 for skill in job_skills if skill in cv_skills_text)
        
        return matched_count / len(job_skills)
    
    def match_cv_with_jobs_base_scores(self, cv_data: Dict, jobs_data: List[Dict]) -> Dict[int, float]:
        """CV'yi iş ilanlarıyla anlamsal olarak karşılaştırıp sadece temel skorları (base_score) döner. (Job ID -> Score)"""
        cv_profile = self.create_cv_profile(cv_data)
        
        base_scores = {}
        
        try:
            model = self._load_model()
            cv_embedding = model.encode([cv_profile])
        except Exception as e:
            logging.error(f"Model yükleme hatası: {e}")
            return {}
        
        for job in jobs_data:
            job_id = job.get('id')
            if not job_id:
                continue
                
            try:
                # İş profili oluştur
                job_profile = self.create_job_profile(job)
                
                # Temel benzerlik skoru
                job_embedding = model.encode([job_profile])
                similarity = cosine_similarity(cv_embedding, job_embedding)[0][0]
                base_score = float(similarity * 100)
                
                base_scores[job_id] = base_score
                
            except Exception as e:
                logging.error(f"Job matching error for job {job_id}: {e}")
                base_scores[job_id] = 0.0
                
        return base_scores
    
    def match_job_with_cvs_base_scores(self, job_data: Dict, cvs_data: List[Dict]) -> Dict[int, float]:
        """Bir iş ilanını birden fazla CV ile model kullanarak anlamsal olarak karşılaştırır 
        ve sadece temel benzerlik (base_score) skorlarını döndürür. (CV ID -> Score)"""
        job_profile = self.create_job_profile(job_data)
        
        # Model'i yükle ve iş ilanını SADECE BİR KERE vektör uzayına çevir
        try:
            model = self._load_model()
            job_embedding = model.encode([job_profile])
        except Exception as e:
            logging.error(f"Model yükleme veya iş ilanı kodlama hatası: {e}")
            job_embedding = None

        base_scores = {}
        
        for cv_data in cvs_data:
            cv_id = cv_data.get('id')
            if not cv_id:
                continue
                
            try:
                cv_profile = self.create_cv_profile(cv_data)
                
                # Temel benzerlik skoru (Kayıtlı job embedding kullanılarak)
                base_score = 0.0
                if job_embedding is not None:
                    cv_embedding = model.encode([cv_profile])
                    similarity = cosine_similarity(cv_embedding, job_embedding)[0][0]
                    base_score = float(similarity * 100)
                
                base_scores[cv_id] = base_score
                
            except Exception as e:
                logging.error(f"CV eşleştirme hatası (CV ID: {cv_id}): {e}")
                base_scores[cv_id] = 0.0
                
        return base_scores
    
    def get_top_matches(self, cv_data: Dict, jobs_data: List[Dict], limit: int = 10) -> List[Dict]:
        """En uygun iş ilanlarını getir"""
        matches = self.match_cv_with_jobs(cv_data, jobs_data)
        
        top_matches = []
        for job, score in matches[:limit]:
            job_with_score = job.copy()
            job_with_score['match_score'] = round(score, 2)
            top_matches.append(job_with_score)
        
        return top_matches

# Global matcher instance - Lazy loading için boş başlat
matcher = None

def get_matcher():
    global matcher
    if matcher is None:
        matcher = CVJobMatcher()
    return matcher
import os
import requests
import logging
import re
import math
from typing import List, Dict
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

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

logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv("HF_TOKEN")
HF_EMBEDDING_API = "https://api-inference.huggingface.co/models/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

class CVJobMatcher:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        
    def get_embedding(self, text: str) -> List[float]:
        """Hugging Face API'den metin embedding'i al"""
        if not text or not text.strip():
            return []
        
        try:
            response = requests.post(
                HF_EMBEDDING_API,
                headers=self.headers,
                json={"inputs": text[:512]},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0] if isinstance(result[0], list) else result
                return []
            else:
                logger.error(f"HF Embedding API error {response.status_code}: {response.text[:200]}")
                return []
        except Exception as e:
            logger.error(f"HF API connection error: {e}")
            return []
        
    def preprocess_text(self, text: str) -> str:
        """Metni temizle ve normalize et"""
        if not text:
            return ""
        
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_skills_and_keywords(self, text: str) -> List[str]:
        """Metinden beceri ve anahtar kelimeleri çıkar"""
        processed_text = self.preprocess_text(text)
        tokens = word_tokenize(processed_text)
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
        """İki profil arasındaki benzerlik skorunu HF API ile hesapla"""
        try:
            cv_embedding = self.get_embedding(cv_profile)
            job_embedding = self.get_embedding(job_profile)
            
            if not cv_embedding or not job_embedding:
                logger.warning("Could not get embeddings from HF API")
                return 0.0
            
            # Cosine similarity manuel hesapla
            dot_product = sum(a * b for a, b in zip(cv_embedding, job_embedding))
            cv_mag = math.sqrt(sum(x**2 for x in cv_embedding))
            job_mag = math.sqrt(sum(x**2 for x in job_embedding))
            
            if cv_mag == 0 or job_mag == 0:
                return 0.0
            
            similarity = dot_product / (cv_mag * job_mag)
            return float(max(0, similarity * 100))
            
        except Exception as e:
            logger.error(f"Similarity calculation error: {e}")
            return 0.0
    
    def calculate_critical_skill_penalty(self, cv_data: Dict, job_data: Dict) -> float:
        """Kritik beceri uyumsuzluğu için VETO sistemi"""
        
        education_penalty = self._check_education_requirement(cv_data, job_data)
        if education_penalty <= -50:
            logger.info(f"EDUCATION VETO: Penalty = {education_penalty}")
            return education_penalty
        
        cv_skills_text = f"{cv_data.get('skills', '')} {cv_data.get('experience', '')} {cv_data.get('summary', '')}".lower()
        job_profile_text = f"{job_data.get('title', '')} {job_data.get('description', '')} {job_data.get('requirements', '')} {job_data.get('skills_required', '')}".lower()
        
        tech_keywords = ['developer', 'engineer', 'programmer', 'software', 'code', 'programming', 'mühendis', 'geliştirici', 'yazılım']
        is_tech_cv = any(keyword in cv_skills_text for keyword in tech_keywords)
        
        matched_role = None
        matched_config = None
        
        for role, config in CRITICAL_SKILLS.items():
            role_in_job = any(keyword in job_profile_text for keyword in config['keywords'])
            if role_in_job:
                matched_role = role
                matched_config = config
                break
        
        if matched_role and matched_config:
            logger.info(f"DEBUG - '{matched_role}' rolü iş ilanında tespit edildi.")
            
            if not matched_config['required']:
                if matched_role not in ['Non-Tech'] and is_tech_cv:
                    logger.info(f"VETO: Teknoloji CV'si, '{matched_role}' rolü ile uyumsuz.")
                    return -100
                return 0.0
            
            matched_skills = [skill for skill in matched_config['required'] if skill in cv_skills_text]
            matched_count = len(matched_skills)
            
            logger.info(f"DEBUG - Aranan: {matched_config['required'][:5]}...")
            logger.info(f"DEBUG - Bulunan: {matched_skills}")
            logger.info(f"DEBUG - Eşleşme Sayısı: {matched_count}")
            
            if matched_count == 0:
                logger.info(f"VETO: İş ilanı '{matched_role}' rolünü istiyor ancak CV'de hiçbir kritik beceri bulunamadı.")
                return matched_config['penalty']
            else:
                logger.info(f"GEÇTİ: {matched_count} kritik beceri bulundu, '{matched_role}' için ceza yok.")
                return 0.0
        
        return 0.0
    
    def _check_education_requirement(self, cv_data: Dict, job_data: Dict) -> float:
        """Eğitim gereksinimi kontrolü - VETO sistemi"""
        
        cv_education = cv_data.get('education', '').lower()
        job_text = f"{job_data.get('title', '')} {job_data.get('description', '')} {job_data.get('requirements', '')}".lower()
        
        logger.info(f"EDUCATION CHECK - CV: {cv_education[:50]}...")
        logger.info(f"EDUCATION CHECK - Job: {job_text[:50]}...")
        
        is_tech_job = any(keyword in job_text for keyword in TECH_JOB_KEYWORDS)
        logger.info(f"EDUCATION CHECK - Is tech job: {is_tech_job}")
        
        if is_tech_job:
            has_tech_education = any(keyword in cv_education for keyword in TECH_EDUCATION_KEYWORDS)
            logger.info(f"EDUCATION CHECK - Has tech education: {has_tech_education}")
            
            if has_tech_education:
                logger.info(f"EDUCATION PASS: Teknik iş ilanı ve teknik eğitim mevcut.")
                return 0.0

            has_non_tech_education = any(keyword in cv_education for keyword in NON_TECH_EDUCATION_KEYWORDS)
            logger.info(f"EDUCATION CHECK - Has non-tech education: {has_non_tech_education}")
            
            if has_non_tech_education:
                logger.info(f"EDUCATION VETO: Teknik iş ilanı, uyumsuz eğitim alanı - CV: {cv_education}")
                return -100
            
            logger.info(f"EDUCATION WARNING: Teknik iş ilanı, eğitim alanı belirsiz - CV: {cv_education}")
            return -90
        
        return 0.0
    
    def calculate_skill_match_bonus(self, cv_skills: List[str], job_skills: List[str]) -> float:
        """Beceri eşleşme bonusu hesapla"""
        if not cv_skills or not job_skills:
            return 0.0
        
        cv_skills_norm = [skill.lower().strip() for skill in cv_skills]
        job_skills_norm = [skill.lower().strip() for skill in job_skills]
        
        matches = len(set(cv_skills_norm) & set(job_skills_norm))
        bonus = min((matches / len(job_skills_norm)) * 20, 20)
        
        return bonus
    
    def calculate_skill_match_ratio(self, cv_data: Dict, job_data: Dict) -> float:
        """Beceri eşleşme oranını hesapla (0.0 - 1.0)"""
        cv_skills_text = f"{cv_data.get('skills', '')} {cv_data.get('experience', '')}".lower()
        job_skills_text = job_data.get('skills_required', '').lower()
        
        if not job_skills_text:
            return 0.5
        
        job_skills = [s.strip() for s in job_skills_text.split(',') if s.strip()]
        
        if not job_skills:
            return 0.5
        
        matched_count = sum(1 for skill in job_skills if skill in cv_skills_text)
        return matched_count / len(job_skills)
    
    def match_cv_with_jobs_base_scores(self, cv_data: Dict, jobs_data: List[Dict]) -> Dict[int, float]:
        """CV'yi iş ilanlarıyla karşılaştırıp temel skorları döner"""
        cv_profile = self.create_cv_profile(cv_data)
        
        base_scores = {}
        cv_embedding = self.get_embedding(cv_profile)
        
        if not cv_embedding:
            logger.error("Could not get CV embedding")
            return {}
        
        for job in jobs_data:
            job_id = job.get('id')
            if not job_id:
                continue
                
            try:
                job_profile = self.create_job_profile(job)
                job_embedding = self.get_embedding(job_profile)
                
                if job_embedding:
                    similarity = self._cosine_similarity(cv_embedding, job_embedding)
                    base_scores[job_id] = float(similarity * 100)
                else:
                    base_scores[job_id] = 0.0
                
            except Exception as e:
                logger.error(f"Job matching error for job {job_id}: {e}")
                base_scores[job_id] = 0.0
                
        return base_scores
    
    def match_job_with_cvs_base_scores(self, job_data: Dict, cvs_data: List[Dict]) -> Dict[int, float]:
        """Bir iş ilanını birden fazla CV ile karşılaştırır"""
        job_profile = self.create_job_profile(job_data)
        job_embedding = self.get_embedding(job_profile)

        base_scores = {}
        
        if not job_embedding:
            logger.error("Could not get job embedding")
            return {}

        for cv_data in cvs_data:
            cv_id = cv_data.get('id')
            if not cv_id:
                continue
                
            try:
                cv_profile = self.create_cv_profile(cv_data)
                cv_embedding = self.get_embedding(cv_profile)
                
                if cv_embedding:
                    similarity = self._cosine_similarity(cv_embedding, job_embedding)
                    base_scores[cv_id] = float(similarity * 100)
                else:
                    base_scores[cv_id] = 0.0
                
            except Exception as e:
                logger.error(f"CV matching error (CV ID: {cv_id}): {e}")
                base_scores[cv_id] = 0.0
                
        return base_scores
    
    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Manuel cosine similarity hesapla"""
        if not vec_a or not vec_b:
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        mag_a = math.sqrt(sum(x**2 for x in vec_a))
        mag_b = math.sqrt(sum(x**2 for x in vec_b))
        
        if mag_a == 0 or mag_b == 0:
            return 0.0
        
        return max(0, dot_product / (mag_a * mag_b))
    
    def get_top_matches(self, cv_data: Dict, jobs_data: List[Dict], limit: int = 10) -> List[Dict]:
        """En uygun iş ilanlarını getir"""
        base_scores = self.match_cv_with_jobs_base_scores(cv_data, jobs_data)
        
        # İş ilanlarını score ile eşleştir
        matches = []
        for job in jobs_data:
            job_id = job.get('id')
            if job_id in base_scores:
                job_with_score = job.copy()
                job_with_score['match_score'] = round(base_scores[job_id], 2)
                matches.append((job_with_score, base_scores[job_id]))
        
        # Score'a göre sırala
        matches.sort(key=lambda x: x[1], reverse=True)
        
        top_matches = [job for job, score in matches[:limit]]
        return top_matches

# Global matcher instance
matcher = None

def get_matcher():
    global matcher
    if matcher is None:
        matcher = CVJobMatcher()
    return matcher

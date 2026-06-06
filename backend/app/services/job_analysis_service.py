import re
import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from ..core.matching_constants import (
    JOB_EDUCATION_PATTERNS, JOB_EXPERIENCE_PATTERNS, JOB_TECH_SKILLS
)

class JobAnalysisService:
    """İş ilanları için özellik çıkarımı servisi"""
    
    def __init__(self):
        # Eğitim gereksinimleri
        self.education_patterns = JOB_EDUCATION_PATTERNS
        
        # Deneyim seviyeleri
        self.experience_patterns = JOB_EXPERIENCE_PATTERNS
        
        # Teknoloji becerileri
        self.tech_skills = JOB_TECH_SKILLS
    
    def extract_job_features(self, job_data: Dict) -> Dict:
        """İş ilanından özellikleri çıkar"""
        
        # Tüm metni birleştir
        full_text = f"{job_data.get('title', '')} {job_data.get('description', '')} {job_data.get('requirements', '')} {job_data.get('skills_required', '')}"
        full_text = full_text.lower()
        
        features = {
            'education_requirements': self._extract_education_requirements(full_text),
            'experience_level': self._extract_experience_level(full_text),
            'required_skills': self._extract_required_skills(full_text),
            'is_mandatory_education': self._check_mandatory_education(full_text),
            'job_category': self._categorize_job(full_text),
            'work_type': job_data.get('work_type', 'office'),
            'salary_range': {
                'min': job_data.get('salary_min'),
                'max': job_data.get('salary_max')
            }
        }
        
        return features
    
    def _extract_education_requirements(self, text: str) -> List[str]:
        """Eğitim gereksinimlerini çıkar"""
        requirements = []
        
        for edu_type, patterns in self.education_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    requirements.append(edu_type)
                    break
        
        return requirements
    
    def _extract_experience_level(self, text: str) -> Optional[str]:
        """Deneyim seviyesini çıkar"""
        for level, patterns in self.experience_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return level
        return None
    
    def _extract_required_skills(self, text: str) -> Dict[str, List[str]]:
        """Gerekli becerileri kategorize ederek çıkar"""
        found_skills = {}
        
        for category, skills in self.tech_skills.items():
            found_skills[category] = []
            for skill in skills:
                if skill.lower() in text:
                    found_skills[category].append(skill)
        
        return found_skills
    
    def _check_mandatory_education(self, text: str) -> bool:
        """Eğitim zorunlu mu kontrol et"""
        mandatory_keywords = [
            'zorunlu', 'şart', 'gerekli', 'required', 'must have',
            'mandatory', 'essential', 'necessary'
        ]
        
        education_keywords = ['mezun', 'diploma', 'degree', 'eğitim']
        
        # Eğitim ve zorunluluk kelimelerinin yakınlığını kontrol et
        for edu_word in education_keywords:
            edu_pos = text.find(edu_word)
            if edu_pos != -1:
                # Eğitim kelimesinin 50 karakter öncesi ve sonrasını kontrol et
                context = text[max(0, edu_pos-50):edu_pos+50]
                if any(mandatory in context for mandatory in mandatory_keywords):
                    return True
        
        return False
    
    def _categorize_job(self, text: str) -> str:
        """İş kategorisini belirle"""
        categories = {
            'software_development': ['developer', 'programmer', 'software', 'yazılım', 'geliştirici'],
            'data_science': ['data scientist', 'data engineer', 'veri bilimci', 'veri mühendis'],
            'devops': ['devops', 'sre', 'infrastructure', 'altyapı'],
            'mobile': ['mobile', 'android', 'ios', 'mobil'],
            'frontend': ['frontend', 'front-end', 'ui/ux'],
            'backend': ['backend', 'back-end', 'api'],
            'management': ['manager', 'lead', 'director', 'müdür', 'yönetici'],
            'other': []
        }
        
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'other'
    
    def validate_cv_job_compatibility(self, cv_features: Dict, job_features: Dict) -> Dict:
        """CV ve iş ilanı uyumluluğunu kontrol et"""
        
        compatibility = {
            'education_match': True,
            'experience_match': True,
            'skills_match': True,
            'overall_compatible': True,
            'blocking_issues': []
        }
        
        # Eğitim uyumluluğu
        if job_features.get('is_mandatory_education') and job_features.get('education_requirements'):
            cv_education = cv_features.get('education_field', '').lower()
            required_education = job_features['education_requirements']
            
            # Mühendislik kontrolü
            if 'engineering' in required_education:
                if 'mühendislik' not in cv_education and 'engineering' not in cv_education:
                    compatibility['education_match'] = False
                    compatibility['blocking_issues'].append('Mühendislik eğitimi gerekli')
        
        # Deneyim uyumluluğu
        job_exp_level = job_features.get('experience_level')
        cv_exp_years = cv_features.get('total_experience_years', 0)
        
        if job_exp_level == 'senior' and cv_exp_years < 5:
            compatibility['experience_match'] = False
            compatibility['blocking_issues'].append('Yetersiz deneyim (5+ yıl gerekli)')
        
        # Genel uyumluluk
        compatibility['overall_compatible'] = (
            compatibility['education_match'] and 
            compatibility['experience_match'] and 
            compatibility['skills_match']
        )
        
        return compatibility

# Global instance
job_analyzer = JobAnalysisService()
from typing import Dict, List, Tuple, Optional
import json
import logging
from datetime import datetime
from ..services.matching_service import get_matcher
from ..core.matching_constants import CRITICAL_SKILLS, TECH_JOB_KEYWORDS, TECH_EDUCATION_KEYWORDS, NON_TECH_EDUCATION_KEYWORDS

class DetailedMatchingService:
    """Detaylı eşleştirme raporu servisi"""
    
    def __init__(self):
        self.matcher = get_matcher()
    
    def analyze_candidate_job_match(self, cv_data: Dict, job_data: Dict, precomputed_base_score: Optional[float] = None) -> Dict:
        """Aday ve iş ilanı arasında detaylı eşleştirme analizi yapar"""
        
        # Temel skorları hesapla
        if precomputed_base_score is not None:
            base_score = precomputed_base_score
        else:
            cv_profile = self.matcher.create_cv_profile(cv_data)
            job_profile = self.matcher.create_job_profile(job_data)
            base_score = self.matcher.calculate_similarity_score(cv_profile, job_profile)
        
        # Beceri analizi
        skill_analysis = self._analyze_skills(cv_data, job_data)
        
        # Eğitim analizi
        education_analysis = self._analyze_education(cv_data, job_data)
        
        # Deneyim analizi
        experience_analysis = self._analyze_experience(cv_data, job_data)
        
        # Kritik beceri analizi
        critical_analysis = self._analyze_critical_requirements(cv_data, job_data)
        
        # Final skor hesaplama
        final_score = self._calculate_final_score(
            base_score, skill_analysis, education_analysis, 
            experience_analysis, critical_analysis
        )
        
        # Skor etiketi ve özet metni oluştur
        score_label = self._get_score_label(final_score)
        summary_text = self._generate_summary_text(
            final_score, skill_analysis, education_analysis, critical_analysis, experience_analysis
        )
        
        return {
            "overall_score": round(final_score, 2),
            "score_label": score_label,
            "summary_text": summary_text,
            "base_similarity": round(base_score, 2),
            "skill_analysis": skill_analysis,
            "education_analysis": education_analysis,
            "experience_analysis": experience_analysis,
            "critical_analysis": critical_analysis,
            "recommendations": self._generate_recommendations(
                skill_analysis, education_analysis, experience_analysis, critical_analysis
            )
        }
    
    def _analyze_skills(self, cv_data: Dict, job_data: Dict) -> Dict:
        """Beceri eşleştirme analizi - CV'nin tüm metninde arama yapar"""
        import re
        job_skills_text = job_data.get('skills_required', '')
        
        # Eğer özel yetenek alanı boşsa, açıklamadan yetenek benzeri kelimeleri çıkarmaya çalış (Fallback)
        if not job_skills_text:
            desc = job_data.get('description', '') + ' ' + job_data.get('requirements', '')
            if desc.strip():
                # Yaygın yetenek kelimelerini description içinden ayıkla (basit bir fallback)
                tech_words = ["python", "java", "react", "node", "sql", "aws", "docker", "excel", "agile", "scrum", "marketing", "seo", "sales", "html", "css", "javascript"]
                found_skills = [w for w in tech_words if w.lower() in desc.lower()]
                if found_skills:
                    job_skills_text = ", ".join(found_skills)
            
        if not job_skills_text:
            return {"score": 15, "matched_skills": [], "missing_skills": [], "extra_skills": [], "match_percentage": 60}

        # CV'nin tüm metni: skills + experience + summary
        cv_full_text = ' '.join(filter(None, [
            cv_data.get('skills', ''),
            cv_data.get('experience', ''),
            cv_data.get('summary', '')
        ])).lower()

        job_skills = [s.strip().lower() for s in job_skills_text.split(',') if s.strip()]
        cv_skills_list = [s.strip().lower() for s in cv_data.get('skills', '').split(',') if s.strip()]

        matched_skills = []
        missing_skills = []
        for skill in job_skills:
            pattern = r'(?<![\w-])' + re.escape(skill) + r'(?![\w-])'
            if re.search(pattern, cv_full_text):
                matched_skills.append(skill)
            else:
                missing_skills.append(skill)

        extra_skills = list(set(cv_skills_list) - set(job_skills))
        match_percentage = (len(matched_skills) / len(job_skills)) * 100 if job_skills else 0
        score = min((match_percentage / 100) * 25, 25)

        return {
            "score": round(score, 2),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "extra_skills": extra_skills,
            "match_percentage": round(match_percentage, 2)
        }
    
    def _analyze_education(self, cv_data: Dict, job_data: Dict) -> Dict:
        """Eğitim uyumluluk analizi"""
        cv_education = cv_data.get('education', '').lower()
        job_text = f"{job_data.get('title', '')} {job_data.get('description', '')} {job_data.get('requirements', '')}".lower()
        
        # İş teknik mi?
        is_tech_job = any(keyword in job_text for keyword in TECH_JOB_KEYWORDS)
        
        # CV'de teknik eğitim var mı?
        has_tech_education = any(keyword in cv_education for keyword in TECH_EDUCATION_KEYWORDS)
        
        # CV'de teknik olmayan eğitim var mı?
        has_non_tech_education = any(keyword in cv_education for keyword in NON_TECH_EDUCATION_KEYWORDS)
        
        if is_tech_job:
            if has_tech_education:
                return {
                    "score": 25,
                    "status": "excellent",
                    "message": "Teknik eğitim geçmişi iş gereksinimleriyle mükemmel uyumlu",
                    "education_type": "technical",
                    "job_type": "technical"
                }
            elif has_non_tech_education:
                return {
                    "score": 0,
                    "status": "poor",
                    "message": "Teknik iş için uyumsuz eğitim geçmişi",
                    "education_type": "non-technical",
                    "job_type": "technical"
                }
            else:
                return {
                    "score": 10,
                    "status": "uncertain",
                    "message": "Eğitim geçmişi belirsiz, teknik iş için risk",
                    "education_type": "unknown",
                    "job_type": "technical"
                }
        else:
            return {
                "score": 20,
                "status": "good",
                "message": "Eğitim geçmişi iş gereksinimleriyle uyumlu",
                "education_type": "compatible",
                "job_type": "non-technical"
            }
    
    def _analyze_experience(self, cv_data: Dict, job_data: Dict) -> Dict:
        """Deneyim analizi - Hem yıl hem de alan uyumunu kontrol eder"""
        cv_experience = cv_data.get('experience', '')
        job_title = job_data.get('title', '').lower()
        job_text = f"{job_data.get('description', '')} {job_data.get('requirements', '')}".lower()
        job_experience_level = job_data.get('experience_level', '').lower()
        
        # Deneyim yılını çıkarmaya çalış
        experience_years = self._extract_experience_years(cv_experience)
        
        # İş ilanındaki deneyim seviyesine göre değerlendirme
        required_years = self._get_required_years_by_level(job_experience_level)
        
        # İLGİLİ ALAN DENEYMİ KONTROLÜ
        # İş teknik mi?
        is_tech_job = any(keyword in job_text or keyword in job_title for keyword in TECH_JOB_KEYWORDS)
        
        # CV'de teknik deneyim var mı?
        tech_experience_keywords = [
            'developer', 'engineer', 'programmer', 'software', 'coding', 'programming',
            'data', 'backend', 'frontend', 'fullstack', 'devops', 'ml', 'ai',
            'geliştirici', 'mühendis', 'yazılım', 'veri'
        ]
        has_tech_experience = any(keyword in cv_experience.lower() for keyword in tech_experience_keywords)
        
        # Teknik olmayan deneyim anahtar kelimeleri
        non_tech_experience_keywords = [
            'marketing', 'sales', 'reklam', 'pazarlama', 'satış', 'muhasebe',
            'accounting', 'hr', 'human resources', 'İnsan kaynakları', 'hukuk', 'legal',
            'avukat', 'lawyer', 'doctor', 'doktor', 'teacher', 'öğretmen'
        ]
        has_non_tech_experience = any(keyword in cv_experience.lower() for keyword in non_tech_experience_keywords)
        
        # ALAN UYUMSUZLUĞU KONTROLÜ
        if is_tech_job and has_non_tech_experience and not has_tech_experience:
            # Teknik iş ama sadece teknik olmayan deneyim var
            return {
                "score": 0,
                "status": "poor",
                "message": f"{experience_years} yıl deneyim var ancak teknik alanda değil. İlgili alan deneyimi gerekli.",
                "candidate_years": experience_years,
                "required_years": required_years,
                "experience_level": job_experience_level,
                "field_mismatch": True
            }
        
        # Yıl bazlı değerlendirme (alan uyumluysa)
        if experience_years >= required_years:
            score = 25
            status = "excellent"
            message = f"{experience_years} yıl ilgili alanda deneyim, gereksinimi ({required_years} yıl) karşılıyor"
        elif experience_years >= required_years * 0.7:
            score = 18
            status = "good"
            message = f"{experience_years} yıl deneyim, gereksinime yakın ({required_years} yıl)"
        elif experience_years >= required_years * 0.4:
            score = 10
            status = "fair"
            message = f"{experience_years} yıl deneyim, gereksinimin altında ({required_years} yıl)"
        else:
            score = 5
            status = "poor"
            message = f"{experience_years} yıl deneyim, gereksinimden çok düşük ({required_years} yıl)"
        
        return {
            "score": score,
            "status": status,
            "message": message,
            "candidate_years": experience_years,
            "required_years": required_years,
            "experience_level": job_experience_level,
            "field_mismatch": False
        }
    
    def _analyze_critical_requirements(self, cv_data: Dict, job_data: Dict) -> Dict:
        """Kritik gereksinim analizi"""
        cv_text = f"{cv_data.get('skills', '')} {cv_data.get('experience', '')} {cv_data.get('summary', '')}".lower()
        job_text = f"{job_data.get('title', '')} {job_data.get('description', '')} {job_data.get('requirements', '')}".lower()
        
        # Hangi kritik rol tespit edildi?
        matched_role = None
        matched_config = None
        
        for role, config in CRITICAL_SKILLS.items():
            if any(keyword in job_text for keyword in config['keywords']):
                matched_role = role
                matched_config = config
                break
        
        if not matched_role:
            return {
                "score": 0,
                "status": "neutral",
                "message": "Kritik gereksinim tespit edilmedi",
                "role": None,
                "required_skills": [],
                "found_skills": []
            }
        
        # Gerekli beceriler var mı?
        if not matched_config['required']:
            return {
                "score": 0,
                "status": "neutral",
                "message": f"{matched_role} rolü için özel beceri gereksinimi yok",
                "role": matched_role,
                "required_skills": [],
                "found_skills": []
            }
        
        # Kritik becerileri kontrol et
        found_skills = [skill for skill in matched_config['required'] if skill in cv_text]
        missing_skills = [skill for skill in matched_config['required'] if skill not in cv_text]
        
        if len(found_skills) == 0:
            return {
                "score": -100,
                "status": "critical_fail",
                "message": f"{matched_role} rolü için kritik beceriler eksik",
                "role": matched_role,
                "required_skills": matched_config['required'],
                "found_skills": found_skills,
                "missing_skills": missing_skills
            }
        else:
            coverage = (len(found_skills) / len(matched_config['required'])) * 100
            return {
                "score": 25,
                "status": "excellent",
                "message": f"{matched_role} rolü için kritik beceriler mevcut (%{coverage:.1f} kapsam)",
                "role": matched_role,
                "required_skills": matched_config['required'],
                "found_skills": found_skills,
                "missing_skills": missing_skills,
                "coverage_percentage": round(coverage, 1)
            }
    
    def _calculate_final_score(self, base_score: float, skill_analysis: Dict, 
                              education_analysis: Dict, experience_analysis: Dict, 
                              critical_analysis: Dict) -> float:
        """Final skoru hesapla - Beceri eşleşmesi çarpan olarak kullanılır"""
        
        # Kritik başarısızlık varsa direkt 0
        if critical_analysis.get('score', 0) <= -50:
            return 0.0
        
        # Alan uyumsuzluğu varsa (teknik iş ama teknik olmayan deneyim)
        if experience_analysis.get('field_mismatch', False):
            return 0.0
        
        # Beceri eşleşme oranını hesapla (0.0 - 1.0)
        skill_match_percentage = skill_analysis.get('match_percentage', 0) / 100.0
        
        # Preliminary score (beceri bonusu olmadan)
        preliminary_score = (
            base_score * 0.4 +  # %40 temel benzerlik
            education_analysis.get('score', 0) +  # %25 eğitim
            experience_analysis.get('score', 0)  # %25 deneyim
        )
        
        # EĞER HİÇBİR BECKERİ EŞLEŞMİYORSA, SKORU DRAMATİK OLARAK DÜŞÜR!
        if skill_match_percentage == 0:
            # Anlamsal olarak ne kadar benzer olursa olsun, temel beceriler yoksa skor çok düşüktür
            final_score = preliminary_score * 0.25  # Skorun sadece %25'ini al
            return min(max(final_score, 0), 100)
        
        # Beceri oranı arttıkça, skorun daha büyük bir yüzdesini al ve üzerine bonus ekle
        skill_multiplier = 0.5 + (skill_match_percentage * 0.5)  # 0.5 ile 1.0 arası
        final_score = (preliminary_score * skill_multiplier) + skill_analysis.get('score', 0)
        
        # Kritik beceri bonusu ekle
        if critical_analysis.get('score', 0) > 0:
            final_score += critical_analysis.get('score', 0) * 0.1
        
        return min(max(final_score, 0), 100)
    
    def _get_score_label(self, score: float) -> str:
        """Skora göre etiket döndür"""
        if score >= 75:
            return "Yüksek Uyum"
        elif score >= 50:
            return "Orta Uyum"
        elif score >= 30:
            return "Potansiyel Uyum"
        else:
            return "Düşük Uyum"
    
    def _generate_summary_text(self, score: float, skill_analysis: Dict, 
                              education_analysis: Dict, critical_analysis: Dict,
                              experience_analysis: Dict = None) -> str:
        """Durumu özetleyen metin oluştur"""
        skill_match = skill_analysis.get('match_percentage', 0)
        
        # Alan uyumsuzluğu kontrolü
        if experience_analysis and experience_analysis.get('field_mismatch', False):
            return "Adayın deneyim yılı yeterli ancak ilgili alanda değil. Teknik pozisyon için teknik alan deneyimi gerekli."
        
        if score < 30:
            if skill_match == 0:
                return "Adayın genel deneyimi ve eğitimi pozisyonla anlamsal olarak benzeşiyor, ancak ilanda istenen temel teknik becerilerin hiçbirine sahip değil."
            elif skill_match < 30:
                return "Adayın beceri seti ilanla kısmen örtüşüyor ancak kritik becerilerin çoğu eksik."
            else:
                return "Adayın profili ilanla kısmen uyumlu ancak deneyim veya eğitim açısından eksiklikler var."
        elif score < 50:
            return "Aday potansiyel gösteriyor. Bazı becerilere sahip ancak ek eğitim veya deneyim gerekebilir."
        elif score < 75:
            return "Aday ilanla iyi bir uyum gösteriyor. Çoğu gereksinimi karşılıyor."
        else:
            return "Aday ilanla mükemmel uyum gösteriyor. Tüm temel gereksinimleri karşılıyor."
    
    def _extract_experience_years(self, experience_text: str) -> int:
        """Deneyim metninden yıl sayısını çıkar"""
        if not experience_text:
            return 0
        
        import re
        from datetime import datetime
        
        # "1 yıl", "3 years", "2-4 yıl" gibi kalıpları ara
        patterns = [
            r'(\d+)\s*(?:yıl|year|years)',
            r'(\d+)\s*-\s*(\d+)\s*(?:yıl|year|years)',
        ]
        
        years_found = []
        
        for pattern in patterns:
            matches = re.findall(pattern, experience_text.lower())
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        # Aralık varsa ortalamasını al
                        years_found.append(int((int(match[0]) + int(match[1])) / 2))
                    else:
                        years_found.append(int(match))
        
        # Eğer açık bir yıl bulunduysa, en büyüğünü al
        if years_found:
            return max(years_found)
        
        # Tarih aralıklarından yıl hesapla (2020 - 2023) veya (Jan 2020 - Dec 2023)
        date_patterns = [
            r'\((\d{4})\s*-\s*(\d{4}|Present|present|Günümüz|günümüz)\)',
            r'\((\w+\s+\d{4})\s*-\s*(\w+\s+\d{4}|Present|present|Günümüz|günümüz)\)'
        ]
        
        total_years = 0
        current_year = datetime.now().year
        
        for pattern in date_patterns:
            matches = re.findall(pattern, experience_text)
            for match in matches:
                start_str, end_str = match
                
                # Başlangıç yılını çıkar
                start_year_match = re.search(r'\d{4}', start_str)
                if not start_year_match:
                    continue
                start_year = int(start_year_match.group())
                
                # Bitiş yılını çıkar
                if 'present' in end_str.lower() or 'günümüz' in end_str.lower():
                    end_year = current_year
                else:
                    end_year_match = re.search(r'\d{4}', end_str)
                    if not end_year_match:
                        continue
                    end_year = int(end_year_match.group())
                
                # Yıl farkını hesapla
                years_diff = max(0, end_year - start_year)
                total_years += years_diff
        
        if total_years > 0:
            return total_years
        
        # Hiçbir şey bulunamadıysa 0 döndür
        return 0
    
    def _get_required_years_by_level(self, level: str) -> int:
        """Deneyim seviyesine göre gerekli yıl sayısı"""
        level_map = {
            'entry': 0,
            'junior': 1,
            'mid': 3,
            'senior': 5,
            'lead': 7,
            'principal': 10
        }
        
        for key, years in level_map.items():
            if key in level:
                return years
        
        return 2  # Varsayılan
    
    def _generate_recommendations(self, skill_analysis: Dict, education_analysis: Dict, 
                                 experience_analysis: Dict, critical_analysis: Dict) -> List[str]:
        """İyileştirme önerileri oluştur"""
        recommendations = []
        
        # Beceri önerileri
        if skill_analysis.get('match_percentage', 0) < 50:
            missing_skills = skill_analysis.get('missing_skills', [])
            if missing_skills:
                recommendations.append(f"Eksik beceriler: {', '.join(missing_skills[:3])}")
        
        # Eğitim önerileri
        if education_analysis.get('status') == 'poor':
            recommendations.append("Teknik eğitim veya sertifikasyon programları önerilir")
        
        # Deneyim önerileri
        if experience_analysis.get('status') == 'poor':
            recommendations.append("Daha fazla deneyim kazanmak için staj veya projeler önerilir")
        
        # Kritik beceri önerileri
        if critical_analysis.get('status') == 'critical_fail':
            missing_critical = critical_analysis.get('missing_skills', [])
            if missing_critical:
                recommendations.append(f"Kritik beceriler eksik: {', '.join(missing_critical[:2])}")
        
        return recommendations

# Global service instance
detailed_matching_service = DetailedMatchingService()
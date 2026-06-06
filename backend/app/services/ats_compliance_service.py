"""
ATS (Applicant Tracking System) Compliance Analysis Service

Bu servis, CV'lerin ATS sistemleri tarafından doğru şekilde okunabilirliğini
ve standartlara uygunluğunu analiz eder.

ATS Standartları:
- Dosya formatı uygunluğu (PDF, DOCX)
- Metin çıkarılabilirliği
- Yapısal bütünlük (bölümler, tarihler, iletişim bilgileri)
- Anahtar kelime yoğunluğu
- Formatlamadan kaynaklı sorunlar
- Okunabilirlik skoru
"""

import re
import logging
from typing import Dict, List, Tuple
from datetime import datetime
import pypdf

logger = logging.getLogger(__name__)


class ATSComplianceAnalyzer:
    """ATS uyumluluk analiz motoru"""
    
    # ATS için kritik bölümler
    CRITICAL_SECTIONS = [
        'experience', 'education', 'skills', 'contact'
    ]
    
    # ATS'nin zorlandığı formatlar
    PROBLEMATIC_PATTERNS = {
        'tables': r'\|[\s\S]*?\|',
        'special_chars': r'[★☆●○■□▪▫◆◇△▲▽▼]',
        'graphics': r'[\u2500-\u257F]',  # Box drawing characters
        'complex_bullets': r'[►▸▹▻◄◂◃◅]'
    }
    
    # Minimum içerik gereksinimleri
    MIN_REQUIREMENTS = {
        'total_words': 100,
        'experience_entries': 1,
        'education_entries': 1,
        'skills_count': 3,
        'contact_fields': 2  # email + phone
    }
    
    def __init__(self):
        self.analysis_results = {}
    
    def analyze_cv(self, cv_text: str, file_path: str, extracted_data: Dict) -> Dict:
        """
        CV'nin ATS uyumluluğunu kapsamlı analiz eder
        
        Args:
            cv_text: PDF'den çıkarılan ham metin
            file_path: CV dosya yolu
            extracted_data: cv_service'den gelen yapısal veri
            
        Returns:
            Detaylı ATS uyumluluk raporu
        """
        logger.info("ATS uyumluluk analizi başlatılıyor...")
        
        results = {
            'overall_score': 0,
            'compliance_level': '',
            'issues': [],
            'warnings': [],
            'recommendations': [],
            'section_scores': {},
            'details': {}
        }
        
        # 1. Dosya Formatı Analizi
        file_score, file_issues = self._analyze_file_format(file_path)
        results['section_scores']['file_format'] = file_score
        results['issues'].extend(file_issues)
        
        # 2. Metin Çıkarılabilirlik Analizi
        text_score, text_issues = self._analyze_text_extractability(cv_text)
        results['section_scores']['text_quality'] = text_score
        results['issues'].extend(text_issues)
        
        # 3. Yapısal Bütünlük Analizi
        structure_score, structure_issues = self._analyze_structure(extracted_data)
        results['section_scores']['structure'] = structure_score
        results['issues'].extend(structure_issues)
        
        # 4. İletişim Bilgileri Analizi
        contact_score, contact_issues = self._analyze_contact_info(extracted_data)
        results['section_scores']['contact_info'] = contact_score
        results['issues'].extend(contact_issues)
        
        # 5. Tarih Formatı Analizi
        date_score, date_issues = self._analyze_date_formats(extracted_data)
        results['section_scores']['date_format'] = date_score
        results['issues'].extend(date_issues)
        
        # 6. Anahtar Kelime Yoğunluğu Analizi
        keyword_score, keyword_warnings = self._analyze_keyword_density(cv_text, extracted_data)
        results['section_scores']['keyword_density'] = keyword_score
        results['warnings'].extend(keyword_warnings)
        
        # 7. Formatlamadan Kaynaklı Sorunlar
        format_score, format_issues = self._analyze_formatting_issues(cv_text)
        results['section_scores']['formatting'] = format_score
        results['issues'].extend(format_issues)
        
        # 8. Bölüm Tespiti Analizi
        section_score, section_issues = self._analyze_section_detection(cv_text)
        results['section_scores']['section_clarity'] = section_score
        results['issues'].extend(section_issues)
        
        # 9. Genel Skor Hesaplama
        overall_score = self._calculate_overall_score(results['section_scores'])
        results['overall_score'] = overall_score
        results['compliance_level'] = self._get_compliance_level(overall_score)
        
        # 10. Öneriler Oluştur
        results['recommendations'] = self._generate_recommendations(results)
        
        # 11. Detaylı İstatistikler
        results['details'] = self._generate_statistics(cv_text, extracted_data)
        
        logger.info(f"ATS analizi tamamlandı. Genel skor: {overall_score}/100")
        return results
    
    def _analyze_file_format(self, file_path: str) -> Tuple[int, List[Dict]]:
        """Dosya formatı uygunluğunu kontrol eder"""
        score = 100
        issues = []
        
        if not file_path:
            return 0, [{'severity': 'critical', 'message': 'Dosya yolu bulunamadı'}]
        
        # PDF analizi
        if file_path.lower().endswith('.pdf'):
            try:
                with open(file_path, 'rb') as f:
                    pdf_reader = pypdf.PdfReader(f)
                    
                    # Sayfa sayısı kontrolü
                    page_count = len(pdf_reader.pages)
                    if page_count > 3:
                        score -= 10
                        issues.append({
                            'severity': 'warning',
                            'message': f'CV {page_count} sayfa. ATS sistemleri genellikle 1-2 sayfalık CV\'leri tercih eder.',
                            'category': 'file_format'
                        })
                    
                    # PDF metadata kontrolü
                    metadata = pdf_reader.metadata
                    if metadata and metadata.get('/Creator'):
                        creator = str(metadata.get('/Creator', '')).lower()
                        # Görsel tasarım araçları ATS için sorunlu olabilir
                        if any(tool in creator for tool in ['photoshop', 'illustrator', 'indesign', 'canva']):
                            score -= 15
                            issues.append({
                                'severity': 'warning',
                                'message': f'CV görsel tasarım aracı ({creator}) ile oluşturulmuş. ATS sistemleri metin tabanlı PDF\'leri tercih eder.',
                                'category': 'file_format'
                            })
                    
            except Exception as e:
                score -= 20
                issues.append({
                    'severity': 'error',
                    'message': f'PDF dosyası analiz edilemedi: {str(e)}',
                    'category': 'file_format'
                })
        
        elif file_path.lower().endswith('.docx'):
            score = 95  # DOCX genellikle ATS uyumludur
        else:
            score = 0
            issues.append({
                'severity': 'critical',
                'message': 'Desteklenmeyen dosya formatı. PDF veya DOCX kullanın.',
                'category': 'file_format'
            })
        
        return score, issues
    
    def _analyze_text_extractability(self, cv_text: str) -> Tuple[int, List[Dict]]:
        """Metnin ATS tarafından okunabilirliğini kontrol eder"""
        score = 100
        issues = []
        
        if not cv_text or len(cv_text.strip()) < 100:
            return 0, [{
                'severity': 'critical',
                'message': 'CV\'den yeterli metin çıkarılamadı. Görsel tabanlı CV kullanıyor olabilirsiniz.',
                'category': 'text_quality'
            }]
        
        # Kelime sayısı kontrolü
        word_count = len(cv_text.split())
        if word_count < self.MIN_REQUIREMENTS['total_words']:
            score -= 30
            issues.append({
                'severity': 'error',
                'message': f'CV çok kısa ({word_count} kelime). Minimum {self.MIN_REQUIREMENTS["total_words"]} kelime önerilir.',
                'category': 'text_quality'
            })
        elif word_count < 200:
            score -= 15
            issues.append({
                'severity': 'warning',
                'message': f'CV kısa ({word_count} kelime). Daha detaylı bilgi ekleyin.',
                'category': 'text_quality'
            })
        
        # Okunabilir karakter oranı
        readable_chars = sum(1 for c in cv_text if c.isalnum() or c.isspace() or c in '.,;:!?-')
        total_chars = len(cv_text)
        readable_ratio = readable_chars / total_chars if total_chars > 0 else 0
        
        if readable_ratio < 0.8:
            score -= 20
            issues.append({
                'severity': 'warning',
                'message': f'Metin okunabilirlik oranı düşük (%{readable_ratio*100:.1f}). Özel karakterler veya semboller ATS tarafından okunamayabilir.',
                'category': 'text_quality'
            })
        
        return score, issues
    
    def _analyze_structure(self, extracted_data: Dict) -> Tuple[int, List[Dict]]:
        """CV'nin yapısal bütünlüğünü kontrol eder"""
        score = 100
        issues = []
        
        # Deneyim kontrolü
        experiences = extracted_data.get('experiences', [])
        if not experiences:
            score -= 30
            issues.append({
                'severity': 'error',
                'message': 'İş deneyimi bölümü tespit edilemedi.',
                'category': 'structure'
            })
        elif len(experiences) < self.MIN_REQUIREMENTS['experience_entries']:
            score -= 15
            issues.append({
                'severity': 'warning',
                'message': 'En az bir iş deneyimi girişi olmalı.',
                'category': 'structure'
            })
        
        # Eğitim kontrolü
        educations = extracted_data.get('educations', [])
        if not educations:
            score -= 25
            issues.append({
                'severity': 'error',
                'message': 'Eğitim bölümü tespit edilemedi.',
                'category': 'structure'
            })
        
        # Beceri kontrolü
        skills = extracted_data.get('skills', [])
        if not skills:
            score -= 20
            issues.append({
                'severity': 'error',
                'message': 'Beceri bölümü tespit edilemedi.',
                'category': 'structure'
            })
        elif len(skills) < self.MIN_REQUIREMENTS['skills_count']:
            score -= 10
            issues.append({
                'severity': 'warning',
                'message': f'Sadece {len(skills)} beceri tespit edildi. En az {self.MIN_REQUIREMENTS["skills_count"]} beceri önerilir.',
                'category': 'structure'
            })
        
        # Özet kontrolü
        summary = extracted_data.get('summary', '')
        if not summary or len(summary) < 50:
            score -= 10
            issues.append({
                'severity': 'info',
                'message': 'Profesyonel özet bölümü eksik veya çok kısa.',
                'category': 'structure'
            })
        
        return score, issues
    
    def _analyze_contact_info(self, extracted_data: Dict) -> Tuple[int, List[Dict]]:
        """İletişim bilgilerinin varlığını ve formatını kontrol eder"""
        score = 100
        issues = []
        
        # Email kontrolü
        email = extracted_data.get('email')
        if not email:
            score -= 40
            issues.append({
                'severity': 'critical',
                'message': 'Email adresi tespit edilemedi. ATS sistemleri için zorunludur.',
                'category': 'contact_info'
            })
        else:
            # Email format kontrolü
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                score -= 15
                issues.append({
                    'severity': 'warning',
                    'message': 'Email formatı geçersiz görünüyor.',
                    'category': 'contact_info'
                })
        
        # Telefon kontrolü
        phone = extracted_data.get('phone')
        if not phone:
            score -= 30
            issues.append({
                'severity': 'error',
                'message': 'Telefon numarası tespit edilemedi.',
                'category': 'contact_info'
            })
        
        # İsim kontrolü
        full_name = extracted_data.get('full_name')
        if not full_name or len(full_name) < 3:
            score -= 30
            issues.append({
                'severity': 'error',
                'message': 'Tam ad tespit edilemedi veya çok kısa.',
                'category': 'contact_info'
            })
        
        return score, issues
    
    def _analyze_date_formats(self, extracted_data: Dict) -> Tuple[int, List[Dict]]:
        """Tarih formatlarının tutarlılığını kontrol eder"""
        score = 100
        issues = []
        
        date_formats_found = set()
        invalid_dates = []
        
        # Deneyim tarihlerini kontrol et
        for exp in extracted_data.get('experiences', []):
            start_date = exp.get('start_date', '')
            end_date = exp.get('end_date', '')
            
            if start_date:
                date_format = self._detect_date_format(start_date)
                if date_format:
                    date_formats_found.add(date_format)
                else:
                    invalid_dates.append(start_date)
            
            if end_date and end_date.lower() not in ['present', 'günümüz', 'current', 'halen']:
                date_format = self._detect_date_format(end_date)
                if date_format:
                    date_formats_found.add(date_format)
                else:
                    invalid_dates.append(end_date)
        
        # Eğitim tarihlerini kontrol et
        for edu in extracted_data.get('educations', []):
            start_date = edu.get('start_date', '')
            end_date = edu.get('end_date', '')
            
            if start_date:
                date_format = self._detect_date_format(start_date)
                if date_format:
                    date_formats_found.add(date_format)
            
            if end_date:
                date_format = self._detect_date_format(end_date)
                if date_format:
                    date_formats_found.add(date_format)
        
        # Tutarsız tarih formatları
        if len(date_formats_found) > 2:
            score -= 15
            issues.append({
                'severity': 'warning',
                'message': f'Farklı tarih formatları kullanılmış ({len(date_formats_found)} farklı format). Tutarlı format kullanın (örn: MM/YYYY).',
                'category': 'date_format'
            })
        
        # Geçersiz tarihler
        if invalid_dates:
            score -= 10
            issues.append({
                'severity': 'info',
                'message': f'{len(invalid_dates)} geçersiz tarih formatı tespit edildi.',
                'category': 'date_format'
            })
        
        return score, issues
    
    def _analyze_keyword_density(self, cv_text: str, extracted_data: Dict) -> Tuple[int, List[Dict]]:
        """Anahtar kelime yoğunluğunu ve tekrarını analiz eder"""
        score = 100
        warnings = []
        
        # Beceri tekrarı analizi
        skills = extracted_data.get('skills', [])
        cv_text_lower = cv_text.lower()
        
        skill_mentions = {}
        for skill in skills:
            skill_lower = skill.lower()
            count = cv_text_lower.count(skill_lower)
            skill_mentions[skill] = count
        
        # Hiç geçmeyen beceriler
        unused_skills = [skill for skill, count in skill_mentions.items() if count == 0]
        if unused_skills:
            score -= 10
            warnings.append({
                'severity': 'info',
                'message': f'{len(unused_skills)} beceri CV metninde hiç geçmiyor. Becerileri deneyim bölümünde de kullanın.',
                'category': 'keyword_density'
            })
        
        # Çok az geçen beceriler
        rare_skills = [skill for skill, count in skill_mentions.items() if 0 < count < 2]
        if len(rare_skills) > len(skills) * 0.5:
            score -= 5
            warnings.append({
                'severity': 'info',
                'message': 'Becerilerin çoğu CV\'de sadece bir kez geçiyor. Deneyim açıklamalarında da kullanın.',
                'category': 'keyword_density'
            })
        
        # Anahtar kelime çeşitliliği
        unique_words = set(re.findall(r'\b\w+\b', cv_text_lower))
        total_words = len(cv_text.split())
        diversity_ratio = len(unique_words) / total_words if total_words > 0 else 0
        
        if diversity_ratio < 0.3:
            score -= 10
            warnings.append({
                'severity': 'warning',
                'message': 'Kelime çeşitliliği düşük. Aynı kelimeleri çok tekrar ediyorsunuz.',
                'category': 'keyword_density'
            })
        
        return score, warnings
    
    def _analyze_formatting_issues(self, cv_text: str) -> Tuple[int, List[Dict]]:
        """ATS'nin zorlandığı format sorunlarını tespit eder"""
        score = 100
        issues = []
        
        # Tablo kullanımı
        if re.search(self.PROBLEMATIC_PATTERNS['tables'], cv_text):
            score -= 15
            issues.append({
                'severity': 'warning',
                'message': 'Tablo formatı tespit edildi. ATS sistemleri tabloları doğru okuyamayabilir.',
                'category': 'formatting'
            })
        
        # Özel karakterler ve semboller
        special_chars = re.findall(self.PROBLEMATIC_PATTERNS['special_chars'], cv_text)
        if special_chars:
            score -= 10
            issues.append({
                'severity': 'warning',
                'message': f'{len(set(special_chars))} farklı özel sembol kullanılmış. Basit madde işaretleri (-) kullanın.',
                'category': 'formatting'
            })
        
        # Grafik karakterler
        if re.search(self.PROBLEMATIC_PATTERNS['graphics'], cv_text):
            score -= 10
            issues.append({
                'severity': 'warning',
                'message': 'Grafik/çizgi karakterleri tespit edildi. ATS tarafından okunamayabilir.',
                'category': 'formatting'
            })
        
        # Çok fazla büyük harf kullanımı
        upper_ratio = sum(1 for c in cv_text if c.isupper()) / len(cv_text) if cv_text else 0
        if upper_ratio > 0.15:
            score -= 5
            issues.append({
                'severity': 'info',
                'message': 'Çok fazla büyük harf kullanımı. Normal cümle yapısı tercih edilir.',
                'category': 'formatting'
            })
        
        return score, issues
    
    def _analyze_section_detection(self, cv_text: str) -> Tuple[int, List[Dict]]:
        """Bölüm başlıklarının ATS tarafından tespit edilebilirliğini kontrol eder"""
        score = 100
        issues = []
        
        # Standart bölüm başlıkları
        standard_sections = {
            'experience': [r'\bexperience\b', r'\bwork\s+experience\b', r'\bemployment\b', r'\bdeneyim\b', r'\biş\s+deneyimi\b'],
            'education': [r'\beducation\b', r'\bacademic\b', r'\beğitim\b'],
            'skills': [r'\bskills\b', r'\bcompetencies\b', r'\byetenekler\b', r'\bbeceriler\b'],
            'summary': [r'\bsummary\b', r'\bprofile\b', r'\bobjective\b', r'\bözet\b', r'\bhakkımda\b']
        }
        
        cv_text_lower = cv_text.lower()
        missing_sections = []
        
        for section_name, patterns in standard_sections.items():
            found = any(re.search(pattern, cv_text_lower) for pattern in patterns)
            if not found:
                missing_sections.append(section_name)
        
        if missing_sections:
            score -= len(missing_sections) * 10
            issues.append({
                'severity': 'warning',
                'message': f'Standart bölüm başlıkları eksik: {", ".join(missing_sections)}. ATS sistemleri standart başlıkları arar.',
                'category': 'section_clarity'
            })
        
        # Bölüm başlıklarının netliği
        lines = cv_text.split('\n')
        potential_headers = [line.strip() for line in lines if line.strip() and len(line.strip()) < 50]
        
        # Çok fazla kısa satır (belirsiz yapı)
        if len(potential_headers) > len(lines) * 0.3:
            score -= 10
            issues.append({
                'severity': 'info',
                'message': 'CV yapısı belirsiz görünüyor. Net bölüm başlıkları kullanın.',
                'category': 'section_clarity'
            })
        
        return score, issues
    
    def _detect_date_format(self, date_str: str) -> str:
        """Tarih formatını tespit eder"""
        date_patterns = {
            'MM/YYYY': r'\d{2}/\d{4}',
            'MM-YYYY': r'\d{2}-\d{4}',
            'YYYY-MM': r'\d{4}-\d{2}',
            'Month YYYY': r'[A-Za-z]{3,9}\s+\d{4}',
            'YYYY': r'^\d{4}$'
        }
        
        for format_name, pattern in date_patterns.items():
            if re.search(pattern, date_str):
                return format_name
        
        return None
    
    def _calculate_overall_score(self, section_scores: Dict) -> int:
        """Bölüm skorlarından genel skoru hesaplar"""
        if not section_scores:
            return 0
        
        # Ağırlıklı ortalama
        weights = {
            'file_format': 0.10,
            'text_quality': 0.15,
            'structure': 0.25,
            'contact_info': 0.20,
            'date_format': 0.10,
            'keyword_density': 0.10,
            'formatting': 0.05,
            'section_clarity': 0.05
        }
        
        weighted_sum = 0
        total_weight = 0
        
        for section, score in section_scores.items():
            weight = weights.get(section, 0.1)
            weighted_sum += score * weight
            total_weight += weight
        
        overall = int(weighted_sum / total_weight) if total_weight > 0 else 0
        return max(0, min(100, overall))
    
    def _get_compliance_level(self, score: int) -> str:
        """Skora göre uyumluluk seviyesi döndürür"""
        if score >= 90:
            return "Mükemmel"
        elif score >= 75:
            return "İyi"
        elif score >= 60:
            return "Orta"
        elif score >= 40:
            return "Zayıf"
        else:
            return "Yetersiz"
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Analiz sonuçlarına göre öneriler oluşturur"""
        recommendations = []
        score = results['overall_score']
        
        # Kritik sorunlar için öneriler
        critical_issues = [issue for issue in results['issues'] if issue.get('severity') == 'critical']
        if critical_issues:
            recommendations.append("KRİTİK: " + critical_issues[0]['message'])
        
        # Skor bazlı öneriler
        if score < 60:
            recommendations.append("CV'nizi ATS uyumlu bir şablon kullanarak yeniden oluşturun.")
        
        if results['section_scores'].get('structure', 100) < 70:
            recommendations.append("Deneyim, Eğitim ve Beceriler bölümlerini net başlıklarla ayırın.")
        
        if results['section_scores'].get('contact_info', 100) < 80:
            recommendations.append("İletişim bilgilerinizi (email, telefon) CV'nin üst kısmına ekleyin.")
        
        if results['section_scores'].get('keyword_density', 100) < 70:
            recommendations.append("İş ilanındaki anahtar kelimeleri deneyim açıklamalarınızda kullanın.")
        
        if results['section_scores'].get('formatting', 100) < 80:
            recommendations.append("Karmaşık formatlamadan kaçının. Basit, temiz bir düzen kullanın.")
        
        # Genel öneriler
        if score >= 75:
            recommendations.append("CV'niz ATS sistemleri için uygun. Başvurularınızda kullanabilirsiniz.")
        
        return recommendations[:5]  # En fazla 5 öneri
    
    def _generate_statistics(self, cv_text: str, extracted_data: Dict) -> Dict:
        """Detaylı istatistikler oluşturur"""
        word_count = len(cv_text.split())
        char_count = len(cv_text)
        
        return {
            'word_count': word_count,
            'character_count': char_count,
            'experience_count': len(extracted_data.get('experiences', [])),
            'education_count': len(extracted_data.get('educations', [])),
            'skills_count': len(extracted_data.get('skills', [])),
            'languages_count': len(extracted_data.get('languages', [])),
            'has_summary': bool(extracted_data.get('summary')),
            'has_email': bool(extracted_data.get('email')),
            'has_phone': bool(extracted_data.get('phone')),
            'extraction_method': extracted_data.get('_extraction_method', 'unknown')
        }


# Global instance
ats_analyzer = ATSComplianceAnalyzer()


def analyze_cv_ats_compliance(cv_text: str, file_path: str, extracted_data: Dict) -> Dict:
    """
    CV'nin ATS uyumluluğunu analiz eder (Facade fonksiyon)
    
    Args:
        cv_text: PDF'den çıkarılan ham metin
        file_path: CV dosya yolu
        extracted_data: cv_service'den gelen yapısal veri
        
    Returns:
        ATS uyumluluk raporu
    """
    return ats_analyzer.analyze_cv(cv_text, file_path, extracted_data)

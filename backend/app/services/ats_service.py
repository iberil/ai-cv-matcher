import re
import pdfplumber
import nltk
from typing import List, Dict, Any
from datetime import datetime
import logging
from ..services.hf_service import call_qwen_hf

# NLTK verilerini indir (eğer yoksa)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

logger = logging.getLogger(__name__)

class ATSService:
    # Standart Başlıklar (TR & EN)
    STANDARD_HEADERS = {
        "Deneyim": [r"deneyim", r"iş tecrübesi", r"iş geçmişi", r"experience", r"work experience", r"employment history"],
        "Eğitim": [r"eğitim", r"akademik", r"education", r"academic background", r"qualifications"],
        "Yetenekler": [r"yetenekler", r"beceriler", r"teknik yetenekler", r"skills", r"technical skills", r"competencies"],
        "Projeler": [r"projeler", r"kişisel projeler", r"projects", r"personal projects"],
        "Sertifikalar": [r"sertifikalar", r"kurslar", r"certifications", r"certificates", r"courses"]
    }

    # Eylem Fiilleri (Action Verbs) - TR & EN
    ACTION_VERBS = [
        "geliştirdim", "yönettim", "tasarladım", "uyguladım", "başardım", "koordine ettim", "analiz ettim",
        "hazırladım", "sundum", "optimize ettim", "artırdım", "azalttım", "kurumum", "planladım", "çözdüm",
        "developed", "managed", "designed", "implemented", "achieved", "coordinated", "analyzed",
        "prepared", "presented", "optimized", "increased", "decreased", "established", "planned", "solved",
        "led", "built", "created", "executed", "initiated"
    ]

    # Trend Anahtar Kelimeler (Örnek - Normalde DB'den veya harici bir yerden gelebilir)
    TREND_KEYWORDS = [
        "ai", "machine learning", "python", "javascript", "react", "node.js", "docker", "kubernetes",
        "cloud", "aws", "azure", "devops", "sql", "nosql", "agile", "scrum", "project management",
        "data analysis", "cybersecurity", "frontend", "backend", "fullstack", "typescript", "next.js"
    ]

    @staticmethod
    def analyze_layout(pdf_path: str) -> Dict[str, Any]:
        """pdfplumber kullanarak metin koordinatlarını ve layout'u inceler."""
        layout_score = 100
        feedback = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                has_tables = False
                has_columns = False
                
                for page in pdf.pages:
                    # Tablo kontrolü
                    tables = page.find_tables()
                    if tables:
                        has_tables = True
                    
                    # Sütun kontrolü (X koordinatlarına göre basit bir analiz)
                    words = page.extract_words()
                    if words:
                        x_coords = [w['x0'] for w in words]
                        # Eğer X koordinatları çok dağınıksa veya belirgin gruplar varsa sütunlu olabilir
                        # Basitçe: Sayfanın sol ve sağ yarısında yoğunluk varsa
                        mid_width = page.width / 2
                        left_words = [w for w in words if w['x1'] < mid_width]
                        right_words = [w for w in words if w['x0'] > mid_width]
                        
                        if len(left_words) > 50 and len(right_words) > 50:
                            has_columns = True
                
                if has_tables:
                    layout_score -= 20
                    feedback.append({"type": "warning", "message": "Tablo kullanımı tespit edildi. ATS sistemleri tabloları okumakta zorlanabilir."})
                
                if has_columns:
                    layout_score -= 15
                    feedback.append({"type": "warning", "message": "İki sütunlu tasarım tespit edildi. Bazı eski ATS sistemleri metin sırasını karıştırabilir."})
                
                if total_pages > 2:
                    layout_score -= 10
                    feedback.append({"type": "info", "message": "CV'niz 2 sayfadan uzun. Profesyoneller için ideal olan 1-2 sayfadır."})

        except Exception as e:
            logger.error(f"Layout analizi hatası: {e}")
            layout_score = 50
            feedback.append({"type": "error", "message": "Dosya layout analizi sırasında bir hata oluştu."})

        return {"score": max(0, layout_score), "feedback": feedback}

    @staticmethod
    def check_headers(cv_text: str) -> Dict[str, Any]:
        """Regex ile standart başlıkların varlığını denetler."""
        found_headers = []
        missing_headers = []
        cv_text_lower = cv_text.lower()
        
        for category, patterns in ATSService.STANDARD_HEADERS.items():
            found = False
            for pattern in patterns:
                if re.search(pattern, cv_text_lower):
                    found = True
                    break
            
            if found:
                found_headers.append(category)
            else:
                missing_headers.append(category)
        
        content_score = 100 - (len(missing_headers) * 15)
        feedback = []
        
        for missing in missing_headers:
            feedback.append({"type": "critical", "message": f"'{missing}' başlığı tespit edilemedi veya standart dışı."})
        
        if not missing_headers:
            feedback.append({"type": "success", "message": "Tüm standart bölümler (Deneyim, Eğitim, Yetenekler vb.) başarıyla tespit edildi."})

        return {"score": max(0, content_score), "feedback": feedback, "found_headers": found_headers}

    @staticmethod
    def analyze_action_verbs(cv_text: str) -> Dict[str, Any]:
        """Eylem fiillerinin kullanım oranını ölçer."""
        words = nltk.word_tokenize(cv_text.lower())
        found_verbs = [w for w in words if w in ATSService.ACTION_VERBS]
        verb_count = len(found_verbs)
        
        # Basit bir puanlama: 10+ fiil iyi, altı az
        if verb_count >= 10:
            score = 100
            message = f"Güçlü bir dil kullanılmış. {verb_count} adet eylem fiili tespit edildi."
            type = "success"
        elif verb_count >= 5:
            score = 70
            message = f"Eylem fiili kullanımı yeterli fakat artırılabilir ({verb_count} adet)."
            type = "info"
        else:
            score = 40
            message = f"Eylem fiili kullanımı çok az ({verb_count} adet). Başarılarınızı 'geliştirdim', 'yönettim' gibi fiillerle anlatın."
            type = "warning"
            
        return {"score": score, "count": verb_count, "feedback": [{"type": type, "message": message}]}

    @staticmethod
    def analyze_keywords(cv_text: str) -> Dict[str, Any]:
        """Anahtar kelime yoğunluğunu analiz eder."""
        cv_text_lower = cv_text.lower()
        found_keywords = [kw for kw in ATSService.TREND_KEYWORDS if kw in cv_text_lower]
        
        match_ratio = len(found_keywords) / len(ATSService.TREND_KEYWORDS)
        score = int(match_ratio * 100)
        
        feedback = []
        if score < 30:
            feedback.append({"type": "warning", "message": "Sektörel anahtar kelime kullanımı düşük. Yeteneklerinizi daha detaylı belirtin."})
        elif score > 70:
            feedback.append({"type": "success", "message": "Anahtar kelime yoğunluğu çok iyi."})
        else:
            feedback.append({"type": "info", "message": "Anahtar kelime kullanımı makul."})
            
        return {"score": score, "feedback": feedback, "found_keywords": found_keywords}

    @staticmethod
    def get_ai_career_advice(cv_text: str, analysis_results: Dict) -> str:
        """Qwen üzerinden kişiselleştirilmiş kariyer koçu tavsiyesi getirir."""
        prompt = f"""Bir kariyer koçu olarak, aşağıdaki ATS analiz sonuçlarına göre bu adaya profesyonel ve insancıl bir dille tavsiyeler ver.
        Analiz Sonuçları:
        - Genel ATS Skoru: {analysis_results['overall_score']}
        - Layout Durumu: {analysis_results['layout_score']}
        - Tespit Edilen Sektörel Anahtar Kelimeler: {', '.join(analysis_results.get('found_keywords', []))}
        - Eylem Fiili Sayısı: {analysis_results['action_verb_count']}
        
        Lütfen adaya 3-4 maddelik, motive edici ve somut öneriler sun. Türkçe yanıt ver.
        """
        
        # Qwen servisini çağır
        # Not: Qwen servisi normalde CV extraction için ayarlanmış ama buraya basit bir chat completion olarak kullanabiliriz.
        # hf_service'deki call_qwen_hf fonksiyonu bir CV parser gibi davranıyor, bu yüzden belki direkt requests ile çağırabiliriz veya onu generalize edebiliriz.
        # Şimdilik hf_service'i modifiye etmeden benzer bir mantıkla çalışalım.
        
        try:
            # career-coach için özel bir prompt ile Qwen çağrısı
            # Not: hf_service'deki call_qwen_hf'ye benzer ama mesajlar farklı
            from ..services.hf_service import HF_TOKEN, HF_MODEL, HF_API_URL
            import requests

            headers = {
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": HF_MODEL,
                "messages": [
                    {"role": "system", "content": "Sen profesyonel bir kariyer danışmanısın. Kullanıcıya CV'sini geliştirmesi için İNSANCIL ve PROFESYONEL tavsiyeler verirsin."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            resp = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                return "Şu an Kariyer Koçu servisi meşgul, lütfen daha sonra tekrar deneyiniz."
        except Exception as e:
            logger.error(f"AI Tavsiye hatası: {e}")
            return "Kariyer tavsiyesi oluşturulurken bir teknik sorun oluştu."

    @staticmethod
    def chat_with_career_coach(cv_text: str, analysis_results: Dict, messages: List[Dict[str, str]]) -> str:
        """Qwen üzerinden etkileşimli kariyer koçu sohbeti."""
        system_prompt = f"""Sen profesyonel ve insancıl bir kariyer danışmanısın. Kullanıcıya CV'sini geliştirmesi için tavsiyeler verirsin. Türkçe dilinde yanıt ver.
        Adayın CV ATS Analiz Sonuçları:
        - Genel ATS Skoru: {analysis_results.get('overall_score', 0)}
        - Layout Skoru: {analysis_results.get('layout_score', 0)}
        - Anahtar Kelimeler: {', '.join(analysis_results.get('found_keywords', []))}
        - Eylem Fiili Sayısı: {analysis_results.get('action_verb_count', 0)}
        
        Kullanıcının sorularına kısa, net, samimi ve motive edici yanıtlar ver. Gereksiz uzun cümlelerden kaçın."""
        
        try:
            from ..services.hf_service import HF_TOKEN, HF_MODEL, HF_API_URL
            import requests
            import time

            headers = {
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type": "application/json",
            }
            
            payload_messages = [{"role": "system", "content": system_prompt}]
            
            for msg in messages:
                payload_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
                
            payload = {
                "model": HF_MODEL,
                "messages": payload_messages,
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            # Yedek (Fallback) Model - 72B meşgul olduğunda 7B versiyonu kullanılır
            FALLBACK_MODEL = "Qwen/Qwen2.5-7B-Instruct"
            FALLBACK_API_URL = "https://router.huggingface.co/v1/chat/completions"
            
            max_retries = 2
            
            for attempt in range(max_retries + 1):
                logger.info(f"Kariyer koçu API isteği gönderiliyor... (deneme {attempt + 1})")
                resp = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
                
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                    
                if resp.status_code == 503:
                    logger.warning(f"Model yükleniyor veya meşgul (503). Deneme: {attempt+1}")
                    if attempt < max_retries:
                        time.sleep(5)
                        continue
                    else:
                        logger.warning(f"Ana model yüklenemedi. Yedek (Fallback) modele geçiliyor: {FALLBACK_MODEL}")
                        payload["model"] = FALLBACK_MODEL
                        resp = requests.post(FALLBACK_API_URL, headers=headers, json=payload, timeout=60)
                        if resp.status_code == 200:
                            data = resp.json()
                            return data["choices"][0]["message"]["content"]
                
                logger.error(f"HF API Hata {resp.status_code}: {resp.text}")
                if attempt == max_retries:
                    return "Sistemde anlık bir yoğunluk var, lütfen 1-2 dakika sonra tekrar soru sormayı deneyin."
                    
        except Exception as e:
            logger.error(f"AI Chat hatası: {e}")
            return "Sohbet sırasında bir teknik sorun oluştu, sunuculara ulaşılamıyor."

    def perform_full_analysis(self, cv_text: str, pdf_path: str) -> Dict[str, Any]:
        """Tüm analizleri birleştirir."""
        layout = self.analyze_layout(pdf_path)
        headers = self.check_headers(cv_text)
        verbs = self.analyze_action_verbs(cv_text)
        keywords = self.analyze_keywords(cv_text)
        
        # Ağırlıklı skor hesaplama
        overall_score = int(
            (layout['score'] * 0.25) +
            (headers['score'] * 0.35) +
            (verbs['score'] * 0.20) +
            (keywords['score'] * 0.20)
        )
        
        # Uyumluluk seviyesi
        if overall_score >= 85: level = "Mükemmel"
        elif overall_score >= 70: level = "İyi"
        elif overall_score >= 50: level = "Orta"
        elif overall_score >= 35: level = "Gelişime Açık"
        else: level = "Yetersiz"
        
        all_feedback = layout['feedback'] + headers['feedback'] + verbs['feedback'] + keywords['feedback']
        
        # Sadece hata ve uyarıları "improvement_suggestions" olarak alalım
        suggestions = [f['message'] for f in all_feedback if f['type'] in ['critical', 'warning', 'error']]
        
        results = {
            "overall_score": overall_score,
            "layout_score": layout['score'],
            "content_score": headers['score'],
            "action_verb_count": verbs['count'],
            "improvement_suggestions": suggestions if suggestions else ["CV'niz genel olarak iyi durumda!"],
            "compliance_level": level,
            "feedback": all_feedback,
            "found_keywords": keywords['found_keywords'],
            "analyzed_at": datetime.now()
        }
        
        return results

ats_service = ATSService()

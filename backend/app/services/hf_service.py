"""
Hugging Face Inference API - Qwen2.5-72B-Instruct CV Parser Servisi

Birincil LLM motoru: Qwen/Qwen2.5-72B-Instruct
OpenAI-uyumlu chat completion endpoint kullanır.
"""

import os
import json
import time
import logging
import requests

logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = "Qwen/Qwen2.5-72B-Instruct"
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"

# Sistem promptu: JSON strict mode
SYSTEM_PROMPT = """You are an expert CV/resume parser. Your ONLY task is to extract structured information from CV text and return it as valid JSON.

CRITICAL RULES:
- Return ONLY valid JSON, nothing else - no markdown, no explanations, no ```json blocks
- Never hallucinate information that is not in the CV text
- If a field is not found, use empty string "" or empty array []
- Extract ALL skills you can find, be exhaustive. Look for tools, frameworks, languages, and methodologies.
- Pay special attention to multi-column layouts; ensure text from different columns is processed logically.
- For dates use the format found in the text (e.g. "2020", "Jan 2020", "2018-2022")"""

# Kullanıcı promptu şablonu
USER_PROMPT_TEMPLATE = """Extract ALL structured data from this CV and return as JSON matching this exact schema:

{{
  "full_name": "string - person's full name",
  "email": "string - email address",
  "phone": "string - phone number",
  "summary": "string - professional summary (generate 1-2 sentences if not present)",
  "skills": ["array", "of", "ALL", "skills", "found"],
  "languages": ["Language (Level)", "e.g. English (Native)", "Turkish (B2)"],
  "experiences": [
    {{
      "company": "string - company name only",
      "position": "string - job title only",
      "start_date": "string",
      "end_date": "string or 'Present'",
      "description": "string - responsibilities and achievements"
    }}
  ],
  "educations": [
    {{
      "institution": "string - university/school name ONLY",
      "degree": "string - degree type ONLY (e.g. Bachelor of Science, Master)",
      "field": "string - field of study ONLY (e.g. Computer Science)",
      "start_date": "string",
      "end_date": "string"
    }}
  ]
}}

INSTRUCTIONS:
- full_name: Extract ONLY the person's name. NEVER include headers like "SUMMARY", "WORK EXPERIENCE", or "RESUME" in this field.
- skills: Extract EVERY technical skill, tool, framework, library, programming language, and soft skill. If you see tools like "Snowflake", "dbt", "Apache Airflow", "Informatica", extract them individually.
- educations: NEVER combine institution+degree+field into one field. Use separate fields.
- experiences: Extract ALL work entries with dates. Ensure multi-word job titles and companies are captured fully.

CV TEXT:
{cv_text}"""


def _parse_json_response(raw: str) -> dict | None:
    """LLM yanıtından JSON'u temizler ve parse eder."""
    if not raw:
        return None

    # Markdown kod bloklarını temizle
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0]
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0]

    raw = raw.strip()

    # JSON bloğunu bul
    si = raw.find("{")
    ei = raw.rfind("}") + 1
    if si != -1 and ei > si:
        raw = raw[si:ei]

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        # Kısmi düzeltme dene: trailing comma, unquoted keys
        logger.warning(f"JSON parse hatası, düzeltme deneniyor: {e}")
        try:
            import re
            # Trailing comma temizle
            raw_fixed = re.sub(r',\s*([}\]])', r'\1', raw)
            return json.loads(raw_fixed)
        except Exception:
            logger.error(f"JSON kurtarma başarısız. Ham yanıt (ilk 500): {raw[:500]}")
            return None


def call_qwen_hf(cv_text: str, max_retries: int = 2) -> dict | None:
    """
    Qwen2.5-72B-Instruct ile CV'den yapısal veri çıkarır.

    Args:
        cv_text: PDF'den çıkarılmış düz metin
        max_retries: 503/rate-limit hatalarında yeniden deneme sayısı

    Returns:
        Çıkarılan veri dict'i veya başarısızsa None
    """
    if not HF_TOKEN:
        logger.error("HF_TOKEN bulunamadı! .env dosyasını kontrol edin.")
        return None

    if not cv_text or not cv_text.strip():
        logger.error("CV metni boş!")
        return None

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": HF_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(cv_text=cv_text[:12000]),
            },
        ],
        "max_tokens": 4096,
        "temperature": 0.05,
        "stream": False,
    }

    for attempt in range(max_retries + 1):
        try:
            logger.info(
                f"Qwen2.5 API isteği gönderiliyor... (deneme {attempt + 1}/{max_retries + 1})"
            )
            resp = requests.post(
                HF_API_URL,
                headers=headers,
                json=payload,
                timeout=120,
            )

            # Rate limit / model yükleniyor
            if resp.status_code == 503:
                wait_time = 20 * (attempt + 1)
                logger.warning(
                    f"HF 503 - Model yükleniyor veya meşgul. "
                    f"{wait_time}s bekleniyor..."
                )
                if attempt < max_retries:
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error("Maksimum yeniden deneme sayısına ulaşıldı (503).")
                    return None

            if resp.status_code == 429:
                wait_time = 30 * (attempt + 1)
                logger.warning(f"HF 429 - Rate limit. {wait_time}s bekleniyor...")
                if attempt < max_retries:
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error("Rate limit aşıldı.")
                    return None

            if resp.status_code != 200:
                logger.error(
                    f"HF API HTTP {resp.status_code}: {resp.text[:400]}"
                )
                return None

            data = resp.json()

            # OpenAI-compat response formatı
            try:
                raw_content = data["choices"][0]["message"]["content"].strip()
            except (KeyError, IndexError) as e:
                logger.error(f"Beklenmeyen HF yanıt yapısı: {e} | Yanıt: {str(data)[:300]}")
                return None

            result = _parse_json_response(raw_content)
            if result:
                logger.info("Qwen2.5 başarıyla yanıt verdi ve JSON parse edildi.")
            else:
                logger.error("Qwen2.5 yanıtı JSON'a dönüştürülemedi.")

            return result

        except requests.Timeout:
            logger.error(f"HF API zaman aşımı (deneme {attempt + 1}).")
            if attempt < max_retries:
                time.sleep(10)
                continue
            return None

        except requests.ConnectionError as e:
            logger.error(f"HF API bağlantı hatası: {e}")
            return None

        except Exception as exc:
            logger.error(f"Beklenmeyen hata: {exc}", exc_info=True)
            return None

    return None

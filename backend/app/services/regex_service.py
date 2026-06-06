import re
from transformers import pipeline
from ..core.matching_constants import (
    SKILLS_KEYWORDS, JOB_TITLE_KEYWORDS,
    EDUCATION_KEYWORDS, NEGATIVE_KEYWORDS
)

# NER Pipeline (lazy loading)
ner_pipeline = None

def get_ner_pipeline():
    """NER pipeline'ini lazy loading ile yukler"""
    global ner_pipeline
    if ner_pipeline is None:
        try:
            ner_pipeline = pipeline(
                "ner",
                model="dslim/bert-base-NER",
                aggregation_strategy="none"
            )
        except Exception as e:
            print(f"NER model yuklenemedi: {e}")
            ner_pipeline = False
    return ner_pipeline


def extract_skills_section(text: str) -> list:
    """
    CV'deki SKILLS bolumunden becerileri dogrudan cikarir.
    'Kategori: Beceri1, Beceri2' formati ve madde isaretli listeler desteklenir.
    """
    skills = []

    skills_pattern = (
        r'(?i)(?:technical\s*|core\s*|professioanal\s*)?'
        r'(?:skills?|yetenekler?|beceriler?|competenc(?:ies|e)|expertise|toolstack|tools)'
        r'[\s:(]*\n(.*?)'
        r'(?=\n\s*(?:EDUCATION|E\u011e\u0130T\u0130M|EXPERIENCE|WORK|HISTORY|LANGUAGES|D\u0130LLER|'
        r'CERTIF|SERT\u0130F|AWARD|REFERENCE|INTEREST|HOBBIES|PROJECT|SUMMARY|OBJECTIVE|PROFILE|\Z))'
    )
    match = re.search(skills_pattern, text, re.DOTALL | re.IGNORECASE)

    if match:
        skills_text = match.group(1)
        for line in skills_text.split('\n'):
            line = re.sub(r'^[\s\u2022\u2013\u2014\-\*\u00b7\u25cf\u25e6]+', '', line).strip()
            if not line:
                continue

            if ':' in line:
                _, _, values_part = line.partition(':')
                for item in re.split(r'[,;]', values_part):
                    item = re.sub(r'\s*\([^)]*\)', '', item).strip()
                    if item and 2 <= len(item) <= 60 and not item.isnumeric():
                        skills.append(item)
            else:
                for item in re.split(r'[,;]', line):
                    item = re.sub(r'\s*\([^)]*\)', '', item).strip()
                    if item and 2 <= len(item) <= 60 and not item.isnumeric():
                        skills.append(item)

    return list(dict.fromkeys(skills))[:30]


def extract_summary_with_regex(text: str) -> str:
    """CV'den ozet/summary kismini cikarir"""
    summary_patterns = [
        r'(?i)(?:ozet|summary|objective|profile|hakkinda|about)[\s:]+(.*?)(?=\n\s*(?:deneyim|experience|egitim|education|yetenek|skill|work|is|history)|$)',
        r'(?i)(?:professional|career|personal)\s+(?:summary|objective|statement)[\s:]+(.*?)(?=\n\s*(?:deneyim|experience|egitim|education)|$)'
    ]

    for pattern in summary_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            summary = match.group(1).strip()
            if len(summary) > 20:
                return summary[:500]

    paragraphs = text.split('\n\n')
    for p in paragraphs[:3]:
        p = p.strip()
        if len(p) > 50 and not any(x in p.lower() for x in ['email', 'phone', 'tel', '@', 'university']):
            return p[:500]

    return None


def _split_position_company(line: str):
    """
    'Data Engineer | Consumer Reports' gibi 'Pozisyon | Şirket' veya
    'Şirket | Pozisyon' formatlarını ayırır.
    """
    # Pipe (|) veya uzun tire (–) ile ayrılmış format
    sep_match = re.match(
        r'^(.+?)\s*[|–—]\s*(.+)$', line.strip()
    )
    if sep_match:
        left  = sep_match.group(1).strip()
        right = sep_match.group(2).strip()

        # Sağ taraf şirket gibi görünüyorsa (büyük harf, tek kelime grubu)
        # Genelde: "Pozisyon | Şirket" formatı
        company_kws = ['inc', 'corp', 'llc', 'ltd', 'co', 'company', 'group',
                       'solutions', 'services', 'technologies', 'systems',
                       'associates', 'partners', 'institute', 'foundation',
                       'board', 'bank', 'insurance', 'reports', 'reserve',
                       'şirketi', 'a.ş', 'ltd', 'holding']
        right_lower = right.lower()
        is_right_company = any(kw in right_lower for kw in company_kws)

        job_kws = ['engineer', 'developer', 'manager', 'analyst', 'intern',
                   'director', 'lead', 'architect', 'consultant', 'specialist',
                   'coordinator', 'officer', 'associate', 'scientist', 'designer',
                   'mühendis', 'geliştirici', 'yönetici', 'analist', 'stajyer']
        left_lower = left.lower()
        is_left_job = any(kw in left_lower for kw in job_kws)

        if is_left_job or is_right_company:
            return left, right    # position, company
        else:
            return right, left    # position, company (ters format)

    return line.strip(), ""


def extract_experiences_with_regex(text: str) -> list:
    """Regex ile deneyimleri cikarir"""
    experiences = []

    # Deneyim başlığı — satırın içinde geçmesi yeterli (daha esnek)
    exp_header_pattern = r'(?i)(?:deneyim|experience|work\s*(?:experience|history)?|employment\s*history|is\s*gecmisi|history)'
    header_match = re.search(exp_header_pattern, text)

    start_index = header_match.end() if header_match else 0
    remaining_text = text[start_index:]

    stop_pattern = r'\n\s*(?:EĞİTİM|EDUCATION|ACADEMIC|YETENEKLER|SKILLS|TECHNICAL|SERTİFİKALAR|CERTIFICATES|PROJELER|PROJECTS|DİLLER|LANGUAGES|REFERANSLAR|REFERENCES)\s*(?:|\n)'
    stop_match = re.search(stop_pattern, remaining_text, re.IGNORECASE)

    if stop_match:
        search_text = remaining_text[:stop_match.start()]
    else:
        search_text = remaining_text

    # Evrensel tarih kalıbı: MM/YYYY | M/YYYY | Mon YYYY | YYYY (En-Dash ve Tire destekli)
    date_pattern = (
        r'((?:0[1-9]|1[0-2])\/(?:19|20)\d{2}|(?:[1-9])\/(?:19|20)\d{2}|'
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|'
        r'Oca|Şub|Mar|Nis|May|Haz|Tem|Ağu|Ey|Ek|Ka|Ar)[a-zçğıöşü]*\.?\s*(?:19|20)\d{2}|'
        r'(?:19|20)\d{2})'
        r'\s*[-–]\s*'
        r'((?:0[1-9]|1[0-2])\/(?:19|20)\d{2}|(?:[1-9])\/(?:19|20)\d{2}|'
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|'
        r'Oca|Şub|Mar|Nis|May|Haz|Tem|Ağu|Ey|Ek|Ka|Ar)[a-zçğıöşü]*\.?\s*(?:19|20)\d{2}|'
        r'(?:19|20)\d{2}|günümüz|current|halen|present|devam)'
    )

    matches = list(re.finditer(date_pattern, search_text, re.IGNORECASE))

    for i, match in enumerate(matches):
        start_date = match.group(1)
        end_date   = match.group(2)

        chunk_start = match.end()
        chunk_end   = matches[i + 1].start() if i + 1 < len(matches) else len(search_text)

        # Description: tarih eşleşmesinden sonraki metin
        description_raw = search_text[chunk_start:chunk_end].strip()

        # Description'dan bir sonraki deneyimin başlık satırını temizle
        # (| içeren ve job keyword taşıyan satırları sona doğru kes)
        desc_lines = description_raw.split('\n')
        clean_desc_lines = []
        for dl in desc_lines:
            dl_stripped = dl.strip()
            # Bir sonraki deneyimin başlığı gibi görünen satırı yakala
            if re.match(r'^.+\s*[|–—]\s*.+$', dl_stripped) and not dl_stripped.startswith('•'):
                break  # Bu satır ve sonrası bir sonraki exp'e ait
            clean_desc_lines.append(dl_stripped)
        description_chunk = '\n'.join(clean_desc_lines).strip()[:600]

        # Tarih eşleşmesinden önceki metin → pozisyon + şirket
        pre_text  = search_text[:match.start()]
        pre_lines = [l.strip() for l in pre_text.strip().split('\n') if l.strip()]

        # Lokasyon satırlarını atla (City, ST veya "Seattle, WA" gibi)
        loc_pattern = re.compile(r'^[A-Za-z\s]+,\s*[A-Z]{2}$')
        # Pipe karakteri içeren satırları veya kısa, anlamlı satırları al
        meaningful = [
            l for l in pre_lines
            if len(l) < 100 and not loc_pattern.match(l)
        ]

        position = ""
        company  = ""

        if meaningful:
            last_line = meaningful[-1]
            # "Pozisyon | Şirket" formatı mı?
            if re.search(r'[|–—]', last_line):
                position, company = _split_position_company(last_line)
            else:
                position = last_line
                if len(meaningful) > 1:
                    prev_line = meaningful[-2]
                    if re.search(r'[|–—]', prev_line):
                        _, company = _split_position_company(prev_line)
                    else:
                        company = prev_line

        exp = {
            'company':     company,
            'position':    position,
            'start_date':  start_date,
            'end_date':    end_date,
            'description': description_chunk,
        }
        experiences.append(exp)
        if len(experiences) >= 5:
            break

    return experiences


def extract_educations_with_regex(text: str) -> list:
    """Regex ile egitim bilgilerini cikarir - bolum bazli guclu parser"""
    educations = []

    # Egitim bolumunu bul
    edu_header = re.search(
        r'(?i)(?:e\u011fitim|education|academic|okul)\s*(?:ge\u00e7mi\u015fi|background|history)?\s*(?::\s*\n|\n)',
        text
    )
    if not edu_header:
        edu_header = re.search(r'(?i)\bEDUCATION\b', text)
    if not edu_header:
        return []

    edu_start = edu_header.end()
    remaining = text[edu_start:]

    # Bir sonraki buyuk baslikta dur
    stop = re.search(
        r'\n\s*(?:YETENEKLER|SKILLS|DENEYIM|EXPERIENCE|WORK|D\u0130LLER|LANGUAGES|'
        r'SERT\u0130F|CERTIF|REFERANS|REFERENCE|PROJE|PROJECT|ILGI|INTEREST|HOBBY|HOBBIES)\s*(?::\s*\n|\n)',
        remaining, re.IGNORECASE
    )
    edu_text = remaining[:stop.start()] if stop else remaining

    # Evrensel tarih kalıbı (Eğitim için)
    date_pattern = (
        r'((?:0[1-9]|1[0-2])\/(?:19|20)\d{2}|(?:[1-9])\/(?:19|20)\d{2}|'
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|'
        r'Oca|Şub|Mar|Nis|May|Haz|Tem|Ağu|Ey|Ek|Ka|Ar)[a-zçğıöşü]*\.?\s*(?:19|20)\d{2}|'
        r'(?:19|20)\d{2})'
        r'\s*[-\u2013]\s*'
        r'((?:0[1-9]|1[0-2])\/(?:19|20)\d{2}|(?:[1-9])\/(?:19|20)\d{2}|'
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|'
        r'Oca|Şub|Mar|Nis|May|Haz|Tem|Ağu|Ey|Ek|Ka|Ar)[a-zçğıöşü]*\.?\s*(?:19|20)\d{2}|'
        r'(?:19|20)\d{2}|g\u00fcn\u00fcm\u00fcz|devam|present|halen)'
    )

    degree_kws = ['b.a', 'b.s', 'b.sc', 'm.a', 'm.s', 'm.sc', 'phd', 'ph.d',
                  'bachelor', 'master', 'lisans', 'yuksek lisans', 'onlisans',
                  'associate', 'doktora', 'diploma', 'certificate', 'arts', 'science']
    inst_kws   = ['university', 'universite', 'college', 'institute', 'school',
                  'okul', 'lise', 'academy', 'fakult', 'teknoloji', 'polytechnic']
    field_kws  = ['muhendislik', 'engineering', 'bilgisayar', 'computer', 'makine',
                  'mechanical', 'isletme', 'business', 'fen', 'administration',
                  'matematik', 'math', 'fizik', 'physics', 'kimya', 'chemistry',
                  'ekonomi', 'economics', 'hukuk', 'law', 'tip', 'medicine',
                  'psikoloji', 'psychology', 'sosyoloji', 'sociology', 'marketing']

    lines = [l.strip() for l in edu_text.split('\n') if l.strip()]
    current_edu = None

    for line in lines:
        line_lower = line.lower()

        date_match = re.search(date_pattern, line, re.IGNORECASE)
        is_degree = any(kw in line_lower for kw in degree_kws)
        is_inst   = any(kw in line_lower for kw in inst_kws)
        is_field  = any(kw in line_lower for kw in field_kws)

        # Mevcut kayitta kurum bos ve bu satir kurum ise, doldurup devam et
        if is_inst and current_edu is not None and not current_edu['institution']:
            current_edu['institution'] = line
            continue

        # Yeni derece satiri
        if is_degree and not is_inst:
            if current_edu and (current_edu.get('institution') or current_edu.get('degree')):
                educations.append(current_edu)
            current_edu = {'institution': '', 'degree': line, 'field': '', 'start_date': None, 'end_date': None}
            if is_field:
                current_edu['field'] = line
            continue

        # Hem derece hem kurum hem tarih ayni satirda (veya sadece kurum+tarih)
        if is_inst:
            if current_edu and (current_edu.get('institution') or current_edu.get('degree')):
                educations.append(current_edu)
            
            # Kurum bilgisini temizle (tarih ve pipe sök)
            clean_inst = re.sub(r'\|.*$', '', line).strip()
            if date_match:
                # Tarih desenini kurumdan sil
                clean_inst = re.sub(date_pattern, '', clean_inst, flags=re.IGNORECASE).strip()
            
            current_edu = {
                'institution': clean_inst, 
                'degree': line if is_degree else '', 
                'field': '', 
                'start_date': date_match.group(1) if date_match else None, 
                'end_date': date_match.group(2) if date_match else None
            }
            continue

        # Sadece kurum satiri (degree henuz yok)
        if is_inst and current_edu is None:
            current_edu = {'institution': line, 'degree': '', 'field': '', 'start_date': None, 'end_date': None}
            continue

        if current_edu is not None:
            if is_field and not current_edu['field'] and not is_inst:
                current_edu['field'] = line
            elif date_match:
                current_edu['start_date'] = date_match.group(1)
                current_edu['end_date']   = date_match.group(2)
            elif not current_edu['institution'] and not date_match and len(line) < 80:
                current_edu['institution'] = line

    if current_edu and (current_edu.get('institution') or current_edu.get('degree')):
        educations.append(current_edu)

    return educations[:3]


def extract_skills_with_ner(text: str) -> dict:
    """NER ile yetenekleri, is unvanlarini ve egitim bilgilerini cikarir"""
    skills = set()
    job_titles = set()
    education = set()
    text_lower = text.lower()

    sorted_skills = sorted(SKILLS_KEYWORDS, key=len, reverse=True)

    for skill in sorted_skills:
        pattern = r'(?<![\w-])' + re.escape(skill) + r'(?![\w-])'
        if re.search(pattern, text_lower):
            skills.add(skill.title() if len(skill.split()) == 1 else skill)

    for title in JOB_TITLE_KEYWORDS:
        pattern = r'(?<![\w-])' + re.escape(title) + r'(?![\w-])'
        if re.search(pattern, text_lower):
            job_titles.add(title.title())

    for edu in EDUCATION_KEYWORDS:
        pattern = r'(?<![\w-])' + re.escape(edu) + r'(?![\w-])'
        if re.search(pattern, text_lower):
            education.add(edu.title())

    ner = get_ner_pipeline()
    if ner:
        try:
            entities = ner(text[:2000])
            for entity in entities:
                word = entity['word'].strip()
                word_lower = word.lower()

                if len(word) < 3 or word_lower in NEGATIVE_KEYWORDS:
                    continue

                if any(re.search(r'(?<![\w-])' + re.escape(kw) + r'(?![\w-])', word_lower) for kw in SKILLS_KEYWORDS):
                    skills.add(word)
                elif any(re.search(r'(?<![\w-])' + re.escape(kw) + r'(?![\w-])', word_lower) for kw in JOB_TITLE_KEYWORDS):
                    job_titles.add(word)
                elif any(re.search(r'(?<![\w-])' + re.escape(kw) + r'(?![\w-])', word_lower) for kw in EDUCATION_KEYWORDS):
                    education.add(word)
        except Exception:
            pass

    return {
        'skills': list(skills)[:20],
        'job_titles': list(job_titles)[:10],
        'education': list(education)[:5]
    }


def extract_basic_info_with_regex(text: str) -> dict:
    """Regex ile temel bilgileri cikarir"""
    info = {}

    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, text)
    info['email'] = email_match.group() if email_match else None

    phone_pattern = r'(\+?\d{1,3}[\s-]?)?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}'
    phone_match = re.search(phone_pattern, text)
    info['phone'] = phone_match.group() if phone_match else None

    return info

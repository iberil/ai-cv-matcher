import re
import unicodedata
import pdfplumber
from pypdf import PdfReader
import shutil
import os

def save_temp_file(uploaded_file, filename):
    os.makedirs("temp_uploads", exist_ok=True)
    file_path = os.path.join("temp_uploads", filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(uploaded_file.file, buffer)
    
    return file_path

def cleanup_file(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)

def clean_raw_text_from_pdf(text):
    """
    PDF'ten çıkarılan metindeki temel kodlama hatalarını ve bozuk karakterleri düzeltir.
    """
    if not text:
        return ""
    
    # Adım 1: En yaygın mojibake kalıplarını düzelt
    text = text.replace('â€‹', '')      # Boşluk karakteri hatası
    text = text.replace('Â', '')        # Tek başına anlamsız 'A' sembolü
    text = text.replace('â€™', "'")    # Kesme işareti
    text = text.replace('â€¢', ' ')    # Madde işareti
    text = text.replace('â€"', '-')     # Uzun tire
    text = text.replace('â€', '"')    # Çift tırnak
    text = text.replace('ï¼', '')      # Geniş formatlı karakterler
    
    # Adım 2: Unicode Normalizasyonu (Karakterleri koru)
    try:
        text = unicodedata.normalize('NFC', text)
    except Exception as e:
        print(f"Normalizasyon hatası: {e}")
        pass

    # Adım 3: Görsel gürültü ve yatay çizgileri temizle (Örn: __________, ----------)
    text = re.sub(r'[\-_=\*\.]{5,}', ' ', text)
    
    # Adım 4: Gereksiz boşlukları temizle (Satır yapısını koruyarak)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    return text.strip()


# Bölüm başlıkları — bu kelimeleri içeren satırlar asla birleştirilmez
_SECTION_HEADERS = re.compile(
    r'(?m)^\s*(?:'
    r'work\s*experience|professional\s*experience|employment\s*history|job\s*history|deneyim|iş\s*geçmişi|'
    r'education|academic\s*background|academic\s*history|eğitim|'
    r'skills?|technical\s*skills?|core\s*competencies|yetenekler?|beceriler?|'
    r'languages?|diller?|'
    r'certif|sertifika|sertifikalar|'
    r'projects?|personal\s*projects?|academic\s*projects?|projeler?|'
    r'summary|career\s*objective|professional\s*profile|özet|profil|hakkında|'
    r'references?|referanslar?|'
    r'awards?|honors?|ödüller?|'
    r'interests?|hobbies|activities|hobiler'
    r').*$',
    re.IGNORECASE
)

# Tarih kalıbı — bu satırlar da birleştirilmez
_DATE_LINE = re.compile(
    r'(?:19|20)\d{2}|'
    r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|'
    r'oca|şub|mar|nis|may|haz|tem|ağu|eyl|eki|kas|ara)',
    re.IGNORECASE
)

# Madde işareti ile başlayan satır
_BULLET_LINE = re.compile(r'^\s*[•·▪▸\-\*]\s')

# Satır sonunda cümle bitti mi?
_SENTENCE_END = re.compile(r'[.!?;:]\s*$')

# Satırın başında büyük harf veya sayı var mı? (yeni cümle başlangıcı)
_SENTENCE_START = re.compile(r'^[A-ZÜĞŞİÖÇ\d]')


def join_broken_lines(text: str) -> str:
    """
    PDF'in iki sütunlu layouttan kaynaklanan
    bölük/yarım satırları birleştirerek akıcı paragraflar oluşturur.

    Mantık:
    - Bölüm başlıkları, tarih satırları, madde işaretli satırlar DOKUNULMAZ
    - Önceki satır nokta/soru işareti ile BİTMİYORSA ve mevcut satır
      küçük harfle devam ediyorsa → önceki satıra eklenir (devam cümlesi)
    - Diğer tüm kısa satırlar (< 60 karakter) önceki satıra eklenir
    """
    lines = text.split('\n')
    result = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Boş satır: koru
        if not stripped:
            result.append('')
            continue

        # Bölüm başlığı veya tarih satırı: asla birleştirme
        if _SECTION_HEADERS.match(stripped) or (
            _DATE_LINE.search(stripped) and len(stripped) < 60
        ):
            result.append(stripped)
            continue

        # Madde işaretli satır: asla öncekiyle birleştir, ama kendisi başlangıç noktası
        if _BULLET_LINE.match(stripped):
            result.append(stripped)
            continue

        # İlk satır
        if not result:
            result.append(stripped)
            continue

        prev = result[-1]

        # Önceki satır boşsa veya bölüm başlığıysa: yeni satır ekle
        if not prev or _SECTION_HEADERS.match(prev) or _BULLET_LINE.match(prev):
            result.append(stripped)
            continue

        # Birleştirme kararı:
        # ÖNEMLİ: Mevcut satır bir bölüm başlığıysa ASLA birleştirme
        if _SECTION_HEADERS.match(stripped):
            result.append(stripped)
            continue

        prev_ends_sentence = _SENTENCE_END.search(prev)
        curr_starts_upper = _SENTENCE_START.match(stripped)
        curr_is_short = len(stripped) < 72  # PDF sütun genişliği genelde < 72 karakter

        should_join = False

        if not prev_ends_sentence and curr_is_short and not curr_starts_upper:
            # Önceki cümle tamamlanmamış + devam küçük harfle → birleştir
            should_join = True
        elif not prev_ends_sentence and len(prev) < 72 and not curr_starts_upper:
            # Önceki satır da kısaysa ve büyük harfle başlamıyorsa → birleştir
            should_join = True

        if should_join:
            # Tire ile bitiyorsa boşluksuz, değilse boşlukla birleştir
            if prev.endswith('-'):
                result[-1] = prev[:-1] + stripped
            else:
                result[-1] = prev + ' ' + stripped
        else:
            result.append(stripped)

    # Tekli boş satırları normalize et
    cleaned = '\n'.join(result)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()


def pdf_to_text(file_path: str) -> str:
    """
    PDF'den metin çıkarır. Önce pdfplumber (sütun-farkındalıklı),
    sonra pypdf dener. Her ikisinde de satır birleştirme uygulanır.
    """
    text = ""
    
    # 1. pdfplumber ile sütun farkındalıklı çıkarma
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages[:5]:
                width = page.width
                height = page.height

                # Sayfanın düzenini akıllıca analiz et
                words = page.extract_words()
                if not words:
                    continue

                width = float(page.width)
                height = float(page.height)

                # 1. KESİNTİSİZ KORİDOR (GUTTER) ANALİZİ
                # Sayfanın %20 ile %80'i arasındaki dikey boşlukları tara.
                # Gerçek bir sütun ayrımı, sayfa boyu (en az %70 dikey) hiç kesilmemelidir.
                
                mid_zone_start = width * 0.20
                mid_zone_end = width * 0.80
                
                # Olası dikey kesitleri 5 piksellik adımlarla tara
                potential_gutters = []
                for x in range(int(mid_zone_start), int(mid_zone_end), 5):
                    # Bu dikey x koordinatını kesen kelime var mı?
                    is_interrupted = any(w['x0'] < x < w['x1'] for w in words)
                    if not is_interrupted:
                        potential_gutters.append(x)
                
                best_mid_x = None
                if potential_gutters:
                    # En geniş kesintisiz boşluğu bul (Gutter)
                    # Basitlik için orta noktaya en yakın olanı seç
                    best_mid_x = min(potential_gutters, key=lambda x: abs(x - width/2))

                # 2. KARAR: İki sütunlu mu yoksa hibrit mi?
                # Eğer koridor yoksa veya döküman genelinde kelime dağılımı tek taraflıysa bölme.
                left_words  = [w for w in words if w['x0'] < (best_mid_x or width/2)]
                right_words = [w for w in words if w['x0'] >= (best_mid_x or width/2)]

                is_two_column = (
                    best_mid_x is not None and
                    len(right_words) > 15 and
                    len(left_words) > 15
                )

                if is_two_column:
                    # Güvenli dikey bölme yap
                    left_bbox  = (0, 0, best_mid_x, height)
                    right_bbox = (best_mid_x, 0, width, height)

                    left_page  = page.within_bbox(left_bbox)
                    right_page = page.within_bbox(right_bbox)

                    # Sol sütunu oku, sonra sağ sütunu oku
                    left_text  = left_page.extract_text(x_tolerance=2, y_tolerance=2) or ''
                    right_text = right_page.extract_text(x_tolerance=2, y_tolerance=2) or ''

                    page_text = left_text + '\n\n' + right_text
                else:
                    # Karma veya tek sütunlu yapı - Varsayılan okuma sırasına güven
                    # Sütunları bölme, ama layout=True ile koordinat bazlı okumayı dene
                    page_text = page.extract_text(x_tolerance=3, y_tolerance=3) or ''

                if page_text:
                    cleaned = clean_raw_text_from_pdf(page_text)
                    text += cleaned + '\n'

        if text.strip():
            # Satır birleştirmeyi tüm metin üzerinde uygula
            return join_broken_lines(text)

    except Exception as ex:
        print(f"pdfplumber hata: {ex}")

    # 2. pdfplumber başarısız olursa pypdf dene
    try:
        reader = PdfReader(file_path)
        for page in reader.pages[:5]:
            page_text = page.extract_text()
            if page_text:
                cleaned_text = clean_raw_text_from_pdf(page_text)
                text += cleaned_text + "\n"
        if text.strip():
            return join_broken_lines(text)
    except Exception:
        pass
    
    return ""

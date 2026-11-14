import fitz  # PyMuPDF
import pdfplumber
import re

def load_with_pymupdf(path):
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def load_with_pdfplumber(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def load_with_blocks(path):
    doc = fitz.open(path)
    paragraphs = []
    for page in doc:
        blocks = page.get_text("blocks")
        blocks = sorted(blocks, key=lambda b: (b[1], b[0]))
        for b in blocks:
            text = b[4].strip()
            if text:
                paragraphs.append(text)
    return "\n\n".join(paragraphs)

def clean_spacing_and_hyphens(text: str) -> str:
    # Отладка: покажем фрагменты, где матчится \xad + пробел
    pattern = r'(?<=[a-zA-Z])\u00ad[\u0020\u00a0\u200b\u202f]?(?=[a-zA-Z])'

    # Удаление всех "мягкий перенос + пробел" между буквами
    text = re.sub(pattern, '', text)

    # Удаление дефиса + пробела между буквами
    text = re.sub(r'(?<=[a-zA-Z])- (?=[a-zA-Z])', '', text)

    # Нормализация пробелов
    text = re.sub(r' {3,}', ' ', text)

    return text

def remove_irrelevant_sections(text: str) -> tuple[str, list[str]]:
    """
    Удаляет нерелевантные секции: abstract, keywords, funding, appendix и т.д.
    Возвращает кортеж: (очищенный текст, список удалённых блоков)
    """
    removed_log = []

    def remove_section(text: str, section_keywords: list, direction: str = "start", max_chars: int = 8000):
        lowered = text.lower()
        for kw in section_keywords:
            pattern = re.compile(rf"(?:^|\n)(\d+\.?\s*)?{kw}\s*[\n:]", flags=re.IGNORECASE)
            matches = list(pattern.finditer(lowered))
            for match in matches:
                start = match.start()
                if direction == "start" and start > len(text) * 0.15:
                    continue
                if direction == "end" and start < len(text) * 0.75:
                    continue
                end = len(text)
                next_section = re.search(
                    r"\n\s*(\d+\.?\s+)?(introduction|methods|results|discussion|conclusion)\b",
                    lowered[start:], flags=re.IGNORECASE)
                if next_section:
                    end = start + next_section.start()
                if (end - start) < max_chars:
                    removed_log.append(text[start:end].strip())
                    text = text[:start] + text[end:]
                    lowered = text.lower()
        return text

    text = remove_section(text, ["abstract", "keywords"], direction="start")
    text = remove_section(text, ["funding", "conflict of interest", "acknowledgments"], direction="end")
    text = remove_section(text, ["appendix", "supplementary material", "support"], direction="end")
    return text, removed_log

def split_references(raw_text: str, i: int) -> tuple[str, str]:
    """
    Разделение текста на основную часть и список источников.
    Добавлен дополнительный способ для случая, когда 'References' идёт в одной строке с первой ссылкой.
    Если ни один способ не срабатывает — выбрасывается ошибка с указанием индекса источника.
    """
    lower_text = raw_text.lower()
    markers = ["references", "bibliography"]

    # 1. Явные заголовки 'References' или 'Bibliography'
    for marker in markers:
        pattern = rf"(\n\s*|^\s*){marker}\s*\n"
        match = re.search(pattern, lower_text)
        if match:
            idx = match.start()
            return raw_text[:idx].strip(), raw_text[idx:].strip()

        # Пронумерованные заголовки
        pattern = rf"\n\s*\d+\.?\s+{marker}\s*\n"
        match = re.search(pattern, lower_text)
        if match:
            idx = match.start()
            return raw_text[:idx].strip(), raw_text[idx:].strip()

    # 2. Стиль ссылок [1] Author, ...
    ref_pattern = r"\n\s*\[\d+\]\s+[A-Z][a-z]+,.*\n"
    match = re.search(ref_pattern, raw_text)
    if match:
        idx = match.start()
        return raw_text[:idx].strip(), raw_text[idx:].strip()

    # 3. Новый способ — References в одной строке с первой ссылкой
    flex_pattern = r"(?:\n|^)\s*References\s+[A-Z][a-z]+.*?\(\d{4}\)"
    match = re.search(flex_pattern, raw_text)
    if match:
        idx = match.start()
        return raw_text[:idx].strip(), raw_text[idx:].strip()

    # 4. Если ничего не найдено — выбрасываем кастомную ошибку
    raise RuntimeError(f"❌ Failed to split references in source index {i}: no identifiable reference section found.")

# def repair_fragmented_lines(text: str) -> str:
#     """
#     Склеивает строки, которые были разорваны посреди слов или фраз.
#     Восстанавливает нормальные строки источников из PDF с искажениями.
#     """
#     lines = text.replace("\r", "").split("\n")
#     repaired = []
#     current_line = ""
#
#     for line in lines:
#         stripped = line.strip()
#
#         if not stripped:
#             continue
#
#         # Добавляется в ту же строку, если это:
#         # - часть года, например (2 0 1 3)
#         # - одиночные цифры или символы
#         # - перенос слова с дефисом (напр. "interper-")
#         if (
#             len(stripped) <= 3
#             or re.fullmatch(r"[\d\s]+", stripped)
#             or stripped.endswith("-")
#             or re.match(r"^[)\].,:;-]+$", stripped)
#         ):
#             current_line += " " + stripped
#         elif re.match(r"^[a-zA-Z\.\,\d\-]+$", stripped) and len(stripped.split()) <= 3:
#             current_line += " " + stripped
#         else:
#             if current_line:
#                 repaired.append(current_line.strip())
#             current_line = stripped
#
#     if current_line:
#         repaired.append(current_line.strip())
#
#     return "\n".join(repaired)
#
#
# def normalize_references(raw_text: str) -> list[str]:
#     """
#     Универсальная обработка списка источников:
#     - Разбивает слепленные блоки по номерам (если есть)
#     - ИЛИ по шаблону фамилия + (год), если номеров нет
#     - Склеивает многострочные источники
#     - Прикрепляет DOI, CrossRef, PubMed к предыдущей строке
#     """
#     repaired_text =repair_fragmented_lines(raw_text)
#     text = repaired_text.replace('\r\n', '\n').replace('\r', '\n').strip()
#
#     # Шаг 1 — грубая разбивка по номерам или шаблонам начала
#     split_regex = re.compile(
#         r"""(?=                               # не поглощать совпадение
#             (?:
#                 \n?\s*\(?\d{1,3}\)?[.)]\s      # 1. или (2)
#                 | \[\d+\]\s                   # [3]
#                 | (?<!\w)([A-Z][a-zA-Z\-]+)   # фамилия с заглавной (если без номера)
#                 \s+(?:[A-Z]\.|[A-Z][a-z]+,?)  # инициалы или второй автор
#                 .+?\(\d{4}\)                  # (2021)
#             )
#         )""", re.VERBOSE)
#
#     parts = re.split(split_regex, text)
#
#     cleaned = []
#     buffer = ""
#
#     for part in parts:
#         if not part or not part.strip():
#             continue
#
#         part = part.strip()
#
#         is_new = bool(re.match(r"^(\(?\d+\)?[.)]|\[\d+\])", part)) or bool(re.search(r"\(\d{4}\)", part)) and not buffer
#
#         if is_new:
#             if buffer:
#                 cleaned.append(buffer.strip())
#             buffer = part
#         else:
#             # Добавляем DOI, CrossRef, обычный текст — всё как продолжение
#             buffer += " " + part
#
#     if buffer:
#         cleaned.append(buffer.strip())
#
#     return cleaned


def load_with_columns(path):

    import fitz  # PyMuPDF
    doc = fitz.open(path)
    all_text = []

    for page in doc:
        width = page.rect.width
        blocks = page.get_text("dict")["blocks"]

        # разделение по колонкам
        left = []
        right = []

        for block in blocks:
            if "lines" not in block:
                continue
            x0 = block["bbox"][0]
            text = " ".join(span["text"] for line in block["lines"] for span in line["spans"]).strip()
            if not text:
                continue
            (left if x0 < width / 2 else right).append((block["bbox"][1], text))  # y0, text

        # сортируем по вертикали и собираем
        left = [text for y, text in sorted(left)]
        right = [text for y, text in sorted(right)]

        all_text.extend(left + right)  # сначала левая колонка, потом правая

    raw_text = "\n\n".join(all_text)
    return raw_text


def extract_text_from_pdf(path: str, method: str = "plumber") -> str:
    """
    method: 'plumber' or 'pymupdf'
    """
    if method == "pymupdf":
        return load_with_pymupdf(path)
    elif method == "plumber":
        return load_with_pdfplumber(path)
    elif method == "blocks":
        return load_with_blocks(path)
    elif method == "columns":
        return load_with_columns(path)
    else:
        raise ValueError("Unknown method: choose 'plumber' or 'pymupdf'")

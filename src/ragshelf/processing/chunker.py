import re
import tiktoken
from typing import List, Tuple, Optional
from collections import Counter
from langdetect import detect


def count_tokens(text: str, tokenizer) -> int:
    """Подсчёт токенов в тексте с использованием tiktoken."""
    return len(tokenizer.encode(text))

def smart_merge_numbered_blocks(paragraphs: List[str]) -> List[str]:
    """
    Объединяет многострочные нумерованные списки в один чанк:
    - Начало списка определяется по шаблону '1.', '2.', и т.д.
    - Продолжение объединяется, пока не встретится новый абзац/заголовок.
    """
    merged = []
    buffer = ""
    in_list = False

    for para in paragraphs:
        stripped = para.strip()

        # Начало нового пункта списка
        if re.match(r"^\d+\.", stripped):
            if buffer:
                merged.append(buffer.strip())
            buffer = stripped
            in_list = True

        # Продолжение предыдущего пункта
        elif in_list and not re.match(r"^[A-Z][A-Z\s]{3,}$", stripped):
            buffer += " " + stripped

        else:
            # Заканчиваем список, если был
            if buffer:
                merged.append(buffer.strip())
                buffer = ""
            merged.append(stripped)
            in_list = False

    # Добавим остаток, если был незавершённый список
    if buffer:
        merged.append(buffer.strip())

    return merged


# def final_trim(text: str) -> Tuple[str, List[str]]:
#     removed = []
#
#     # Удаляем DOI и лицензии
#     patterns = [
#         r"https?://\s*doi\.org\S*",
#         r"https?://\s*creativecommons\.org\S*",
#         r"https?://\S+",
#         r"doi:\s*10\.\d{4,9}/[-._;()/:a-z0-9]+"
#     ]
#     for pattern in patterns:
#         matches = re.findall(pattern, text, flags=re.I)
#         for m in matches:
#             removed.append(m)
#         text = re.sub(pattern, '', text, flags=re.I)
#
#     # Удаляем строки типа Revised/Accepted/Published, если почти все слова с заглавной буквы
#     lines = text.splitlines()
#     cleaned = []
#     for line in lines:
#         if len(line) < 300 and re.match(r'^(Revised|Accepted|Published|Copyright):', line.strip()):
#             words = line.strip().split()
#             if not words:
#                 continue
#             words = [w for w in words if re.search(r'[A-Za-z]', w)]
#             capitalized = [w for w in words if w[0].isupper()]
#             if len(capitalized) / len(words) > 0.7:
#                 removed.append(line)
#                 continue
#         cleaned.append(line)
#     text = "\n".join(cleaned)
#     return text.strip(), removed

def final_trim(text: str) -> Tuple[str, List[str]]:
    removed = []

    # Удаляем DOI и лицензии
    patterns = [
        r"https?://\s*doi\.org\S*",
        r"https?://\s*creativecommons\.org\S*",
        r"https?://\S+",
        r"doi:\s*10\.\d{4,9}/[-._;()/:a-z0-9]+"
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, flags=re.I)
        for m in matches:
            removed.append(m)
        text = re.sub(pattern, '', text, flags=re.I)

    # Удаляем мусорные вкрапления в тексте, даже если они не на новой строке
    garbage_phrases = [
        r"Accepted:\s*\d{1,2}\s+\w+\s+\d{4}",
        r"Published:\s*\d{1,2}\s+\w+\s+\d{4}",
        r"Revised:\s*\d{1,2}\s+\w+\s+\d{4}",
        r"Copyright:\s*©\s*\d{4}.*?(?=[A-Z]|\Z)",  # до конца или до следующего слова с большой буквы
        r"Licensee\s+MDPI,\s+Basel,\s+Switzerland"
    ]
    for pattern in garbage_phrases:
        matches = re.findall(pattern, text, flags=re.I)
        for m in matches:
            removed.append(m)
        text = re.sub(pattern, '', text, flags=re.I)

    return text.strip(), removed

def postprocess_chunks(chunks: List[str]) -> Tuple[List[str], List[str]]:
    removed_log = []

    def log(reason: str, text: str):
        removed_log.append(f"[{reason.upper()}] {text.strip()}")

    def is_too_short(text: str, i: int) -> bool:
        words = text.strip().split()
        words = [w for w in words if re.search(r'[A-Za-z]', w)]
        if i < 10:
            return len(words) < 12
        else:
            return len(words) < 9

    def is_journal_meta_block(text: str) -> bool:
        lowered = text.lower()
        meta_keywords = ["vol.", "no.", "nº", "issue", "pages", "issn", "print edition", "anales de psicología"]
        if len(text) > 200:
            return False
        return any(kw in lowered for kw in meta_keywords)

    def is_non_english(text: str) -> bool:
        try:
            lang = detect(text)
            return lang != 'en'
        except:
            return False

    def is_digit_dominant(text: str) -> bool:
        clean = re.sub(r"[^a-zA-Z0-9]", "", text)
        if not clean:
            return False
        digits = sum(c.isdigit() for c in clean)
        return digits / len(clean) > 0.5

    def is_mostly_title_case_words(text: str) -> bool:
        words = text.strip().split()
        words = [w for w in words if re.search(r'[A-Za-z]', w)]
        if not words:
            return False
        title_case_words = [w for w in words if w[0].isupper()]
        return len(title_case_words) / len(words) >= 0.7

    def is_meta_info(text: str) -> bool:
        text = text.strip()
        meta_keywords = [
            "correspondence", "received", "accepted", "published",
            "editor", "funding", "author contributions", "licensee mdpi"
        ]
        if any(text.lower().startswith(word) for word in meta_keywords):
            return True
        return (
            re.match(r"^doi:", text, re.I) or
            re.search(r"https?://doi\.org", text, re.I) or
            re.search(r"https?://creativecommons\.org", text, re.I) or
            re.match(r"^\s*(figure|table|vol\.|issue|legend)\b", text, re.I)
        )

    def is_mostly_uppercase(text: str) -> bool:
        letters = [c for c in text if c.isalpha()]
        return letters and sum(1 for c in letters if c.isupper()) / len(letters) > 0.8

    def is_probably_author_line(text: str) -> bool:
        text = text.strip()
        if not text:
            return False
        name_pattern = re.compile(r"(?:[A-Z][a-z]+\s){1,2}[A-Z][a-z]+")
        matches = name_pattern.findall(text)
        name_words = sum(len(m.split()) for m in matches)
        return name_words / max(1, len(text.split())) >= 0.7

    def is_bibliographic_entry(text: str) -> bool:
        if len(text) > 300:
            return False
        author_like = len(re.findall(r"[A-Z][a-z]+(?:\s+[A-Z]\.|\s*,\s*[A-Z]\.)", text)) >= 2
        has_journal_info = re.search(r"\d{4};\d+", text) or re.search(r"\d{4}\)", text)
        has_doi = re.search(r"doi:\s*10\.\d{4,9}/[-._;()/:a-z0-9]+", text, re.I)
        return (author_like and has_journal_info) or has_doi

    def is_irrelevant_section_header(text: str) -> bool:
        norm = text.strip().lower()
        to_check = ["abstract", "keywords", "key words"]
        # return norm.startswith("abstract") or norm.startswith("keywords") or norm.startswith("key words")
        return any(norm.startswith(check) for check in to_check)

    def is_header_block(text: str, i: int) -> bool:
        if i >= 5:
            return False
        return bool(re.search(
            r"(journal|license|open access|creativecommons|mdpi|basel|editor|funding|@|institute)",
            text, re.I
        ))

    def is_affiliation_line(text: str, i: int) -> bool:
        if i >= 5:
            return False
        return bool(re.search(r"(department|university|via|roma|florence|london|padova)", text, re.I))

    def is_isolated_section_title(text: str) -> bool:
        stripped = text.strip()
        return bool(re.match(r"^\d+(\.\d+)*\s+[\w\s\-]{1,50}$", stripped)) and len(stripped.split()) <= 6

    # def strip_known_meta_links(text: str) -> str:
    #     # Удаляем DOI, CreativeCommons, mdpi, https://...
    #     text = re.sub(r"https?://\s*doi\.org\S*", "", text, flags=re.I)
    #     text = re.sub(r"https?://\s*creativecommons\.org\S*", "", text, flags=re.I)
    #     text = re.sub(r"https?://\S*", "", text)
    #     text = re.sub(r"doi:\s*10\.\d{4,9}/[-._;()/:a-z0-9]+", "", text, flags=re.I)
    #     return text.strip()

    def normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    final = []
    seen = set()

    for i, chunk in enumerate(chunks):
        text = chunk.strip()
        norm = normalize(text)

        if is_too_short(text, i):
            log("too_short", text)
            continue
        if is_mostly_title_case_words(text):
            log("title_case_majority", text)
            continue
        if is_meta_info(text):
            if len(text) < 400:
                log("meta_info", text)
                continue
            else:
                cleaned_text, final_removed = final_trim(text)
                if cleaned_text:
                    final.append(cleaned_text)
                    if final_removed:
                        log("final_trim", " | ".join(final_removed))
                else:
                    log("final_trim_all", text)
                continue
        if is_mostly_uppercase(text):
            log("mostly_uppercase", text)
            continue
        if is_probably_author_line(text):
            log("author_line", text)
            continue
        if is_bibliographic_entry(text):
            log("bibliographic", text)
            continue
        if is_irrelevant_section_header(text):
            log("section_header", text)
            continue
        if is_header_block(text, i):
            if len(text.split()) <= 100:
                log("header_block", text)
                continue
        if is_affiliation_line(text, i):
            log("affiliation_line", text)
            continue
        if is_isolated_section_title(text):
            log("isolated_section_title", text)
            continue

        if is_journal_meta_block(text):
            log("journal_meta", text)
            continue

        if is_non_english(text):
            log("non_english", text)
            continue

        if is_digit_dominant(text):
            log("digit_dominant", text)
            continue

        if norm in seen:
            log("duplicate", text)
            continue

        cleaned_text, final_removed = final_trim(text)
        if cleaned_text:
            final.append(cleaned_text)
            if final_removed:
                log("final_trim", " | ".join(final_removed))
        else:
            log("final_trim_all", text)

        seen.add(norm)

    return final, removed_log


def merge_broken_chunks(chunks: List[str]) -> List[str]:
    """
    Объединяет чанки по условиям:
    1. Если текущий чанк заканчивается на ':' — объединяем со следующим.
    2. Если следующий чанк начинается с маленькой буквы — объединяем.
    """
    merged = []
    i = 0

    while i < len(chunks):
        current = chunks[i].strip()
        i += 1

        while i < len(chunks):
            next_chunk = chunks[i].strip()
            if not next_chunk:
                i += 1
                continue

            # Условия объединения
            first_char = next_chunk.lstrip()[0] if next_chunk.lstrip() else ""
            condition_1 = current.endswith(":")
            condition_2 = first_char.islower()
            condition_3 = first_char in "([{\"“‘'"

            if condition_1 or condition_2 or condition_3:
                current += " " + next_chunk
                i += 1
            else:
                break

        merged.append(current)

    return merged

def split_oversized_chunks(chunks: List[str], tokenizer, max_tokens: int = 512) -> List[str]:
    """
    Разбивает чанки, в которых больше max_tokens токенов, по предложениям.
    Сохраняет порядок: подчанки встают на место исходного чанка, сдвигая остальные.
    Предполагается, что одно предложение не может превышать лимит токенов.
    """
    i = 0
    while i < len(chunks):
        chunk = chunks[i]
        if count_tokens(chunk, tokenizer) <= max_tokens:
            i += 1
            continue

        # 1. Разбиваем на предложения
        sentences = re.split(r'(?<=[.!?])\s+', chunk.strip())

        # 2. Собираем чанки из предложений
        subchunks = []
        current = ""
        for sent in sentences:
            if not sent:
                continue
            tentative = current + " " + sent if current else sent
            if count_tokens(tentative, tokenizer) <= max_tokens:
                current = tentative
            else:
                if current:
                    subchunks.append(current.strip())
                current = sent
        if current:
            subchunks.append(current.strip())

        # 3. Заменяем текущий чанк на несколько подчанков
        chunks.pop(i)
        for sub in reversed(subchunks):
            chunks.insert(i, sub)

        i += len(subchunks)  # переходим к следующему оригинальному чанку

    return chunks

# def additional_trim(chunks: List[str]) -> Tuple[List[str], List[str]]:
#     removed_log = []
#
#     def log(reason: str, text: str):
#         removed_log.append(f"[{reason.upper()}] {text.strip()}")
#
#     def normalize(text: str) -> str:
#         return re.sub(r"\s+", " ", text.strip().lower())
#
#     final = []
#
#     for i, chunk in enumerate(chunks):
#         text = chunk.strip()
#         norm = normalize(text)
#         removed = []
#
#         if norm.startswith("key words:") or norm.startswith("keywords:"):
#             dot_index = text.find('.')
#             if dot_index != -1:
#                 removed_part = text[:dot_index + 1].strip()
#                 text = text[dot_index + 1:].lstrip()
#                 removed.append(removed_part)
#                 if removed:
#                     log("additional_trim", " | ".join(removed))
#             final.append(text.strip())
#             continue
#
#         final.append(text)
#
#     return final, removed_log

def additional_postprocess(chunks: List[str]) -> Tuple[List[str], List[str]]:
    removed_log = []

    def log(reason: str, text: str):
        removed_log.append(f"[{reason.upper()}] {text.strip()}")

    def normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    final = []

    for chunk in chunks:
        text = chunk.strip()
        norm = normalize(text)
        half_index = len(norm) // 2
        second_half = norm[half_index:].lower()

        if "keywords:" in second_half or "key words:" in second_half:
            log("additional_postprocess", text)
            continue

        final.append(text)

    return final, removed_log


def split_text(text: str, max_tokens: int = 512) -> Tuple[List[str], List[str]]:
    """
    Делит текст на абзацы по \n\n и обрезает каждый до max_tokens токенов.
    Также объединяет нумерованные блоки в логические чанки.
    """
    paragraphs = text.split("\n\n")

    tokenizer = tiktoken.get_encoding("cl100k_base")

    # Постобработка: склеить логические списки
    paragraphs = smart_merge_numbered_blocks(paragraphs)

    chunks = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        chunks.append(para)

    final, removed_log = postprocess_chunks(chunks)
    final, additional_removed_log = additional_postprocess(final)
    removed_log.extend(additional_removed_log)
    final = merge_broken_chunks(final)
    final = split_oversized_chunks(final, tokenizer, max_tokens)


    ## ТОЧНО РАБОЧАЯ ВЕРСИЯ
    # final, removed_log = postprocess_chunks(chunks)
    # final = merge_broken_chunks(final)
    # final = split_oversized_chunks(final, tokenizer, max_tokens)

    return final, removed_log

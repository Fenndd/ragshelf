# token_counter.py

import tiktoken

def count_tokens_in_text(text: str, encoding_name: str = "cl100k_base") -> int:
    """
    Подсчитывает количество токенов в строке с помощью tiktoken.

    :param text: Строка, для которой нужно посчитать токены.
    :param encoding_name: Название схемы токенизации (по умолчанию cl100k_base).
    :return: Количество токенов.
    """
    tokenizer = tiktoken.get_encoding(encoding_name)
    return len(tokenizer.encode(text))

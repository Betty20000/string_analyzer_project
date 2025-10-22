import hashlib
from collections import Counter

def analyze_string(value):
    value_stripped = value.strip()
    length = len(value_stripped)
    is_palindrome = value_stripped.lower() == value_stripped[::-1].lower()
    unique_characters = len(set(value_stripped))
    word_count = len(value_stripped.split())
    sha256_hash = hashlib.sha256(value_stripped.encode()).hexdigest()
    character_frequency_map = dict(Counter(value_stripped))

    return {
        "length": length,
        "is_palindrome": is_palindrome,
        "unique_characters": unique_characters,
        "word_count": word_count,
        "sha256_hash": sha256_hash,
        "character_frequency_map": character_frequency_map
    }

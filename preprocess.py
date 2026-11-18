import re
from ml_language import to_english


def limpar_texto(t: str) -> str:
    # ML only: never use this function to create or validate evidence quotes.
    t = str(t)
    t = re.sub(r'http\S+|www\S+', ' ', t)
    t = re.sub(r'\S+@\S+', ' ', t)
    t = to_english(t).lower()
    t = re.sub(r'[^a-zA-ZÀ-ÿ\s+#.]', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()

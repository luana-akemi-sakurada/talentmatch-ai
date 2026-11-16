"""Best-effort minimization, not guaranteed anonymization of free text."""
import re

PATTERNS = (
    r'[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}',
    r'https?://\S+|www\.\S+|(?:linkedin\.com|github\.com)/\S+',
    r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
    r'(?<!\w)(?:\+?55\s*)?\(?\d{2}\)?[\s.-]*\d{4,5}[\s.-]*\d{4}(?!\w)',
    r'\b\d{2}[/.-]\d{2}[/.-]\d{4}\b',
    r'(?im)^\s*(?:nome|name|candidato|candidate|endereço|endereco|address|contato|contact|telefone|phone|cpf|rg|idade|age|gênero|genero|gender|sexo|sex|estado civil|marital status|nacionalidade|nationality|nascimento|date of birth)\s*[:：].*$',
    r'(?im)^\s*(?:rua|avenida|av\.|street|alameda|travessa)\s+.*$',
    r'\b\d{1,2}\s*(?:anos de idade|years old)\b',
)


def minimize(text: str, resume: bool = False) -> tuple[str, int]:
    count = 0
    for pattern in PATTERNS:
        text, found = re.subn(pattern, '[DADO REMOVIDO]', text, flags=re.I)
        count += found
    # Unlabelled names frequently occur on the first resume line. Remove a short
    # alphabetic header conservatively; do not apply this heuristic to the job.
    lines = text.strip().splitlines()
    if resume and lines:
        first = lines[0].strip()
        words = first.split()
        role_words = {'python', 'sql', 'java', 'react', 'analyst', 'analista', 'developer',
                      'desenvolvedor', 'engineer', 'engenheiro', 'currículo', 'curriculo',
                      'resume', 'curriculum', 'vitae', 'data', 'dados', 'skills', 'experiência'}
        looks_like_name = all(w.istitle() or w.lower() in {'de', 'da', 'do', 'dos', 'das'} for w in words)
        if (2 <= len(words) <= 5 and all(w.isalpha() for w in words) and looks_like_name
                and not any(w.casefold() in role_words for w in words)):
            lines[0] = '[CABEÇALHO REMOVIDO]'
            count += 1
    return '\n'.join(lines), count

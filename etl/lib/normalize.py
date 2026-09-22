import unicodedata
import re

# Correções manuais para nomes que divergem entre as fontes (Anuário / TSE / IBGE)
# depois da normalização (maiúsculas, sem acento). Mapeia normalizado_da_fonte -> normalizado_ibge
ALIASES = {
    # TSE grafa "Eldorado dos Carajás" (plural); nome oficial IBGE é "Eldorado do Carajás".
    "ELDORADO DOS CARAJAS": "ELDORADO DO CARAJAS",
}


def normalize(nome: str) -> str:
    if nome is None:
        return ""
    nome = nome.strip().upper()
    nome = unicodedata.normalize("NFKD", nome)
    nome = "".join(c for c in nome if not unicodedata.combining(c))
    nome = nome.replace("-", " ")
    nome = re.sub(r"\s+", " ", nome).strip()
    return ALIASES.get(nome, nome)

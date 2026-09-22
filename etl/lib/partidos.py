# Numeração oficial dos partidos políticos (TSE) vigente nas Eleições Municipais 2024.
# Numeração é nacional e não varia por município.
PARTIDOS = {
    10: ("REPUBLICANOS", "Republicanos"),
    11: ("PP", "Progressistas"),
    12: ("PDT", "Partido Democrático Trabalhista"),
    13: ("PT", "Partido dos Trabalhadores"),
    14: ("PTB", "Partido Trabalhista Brasileiro"),
    15: ("MDB", "Movimento Democrático Brasileiro"),
    18: ("REDE", "Rede Sustentabilidade"),
    19: ("PODE", "Podemos"),
    20: ("PSC", "Partido Social Cristão"),
    21: ("PCB", "Partido Comunista Brasileiro"),
    22: ("PL", "Partido Liberal"),
    23: ("CIDADANIA", "Cidadania"),
    25: ("DC", "Democracia Cristã"),
    27: ("DEMOCRACIA", "Democracia Cristã"),
    28: ("PRTB", "Partido Renovador Trabalhista Brasileiro"),
    29: ("PCO", "Partido da Causa Operária"),
    30: ("NOVO", "Partido Novo"),
    31: ("PMB", "Partido da Mulher Brasileira"),
    33: ("PMN", "Partido da Mobilização Nacional"),
    35: ("PMB", "Partido da Mulher Brasileira"),
    36: ("AGIR", "Agir"),
    40: ("PSB", "Partido Socialista Brasileiro"),
    43: ("PV", "Partido Verde"),
    44: ("UNIÃO", "União Brasil"),
    45: ("PSDB", "Partido da Social Democracia Brasileira"),
    50: ("PSOL", "Partido Socialismo e Liberdade"),
    54: ("PPL", "Partido Pátria Livre"),
    55: ("PSD", "Partido Social Democrático"),
    65: ("PC do B", "Partido Comunista do Brasil"),
    70: ("AVANTE", "Avante"),
    77: ("SOLIDARIEDADE", "Solidariedade"),
    80: ("UP", "Unidade Popular"),
    90: ("PROS", "Partido Republicano da Ordem Social"),
}


def sigla_nome(numero: int):
    if numero in PARTIDOS:
        return PARTIDOS[numero]
    return (f"PARTIDO {numero}", f"Partido nº {numero}")

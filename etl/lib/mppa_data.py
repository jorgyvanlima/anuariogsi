"""Dados estruturados extraídos manualmente do PDF "ALEPA - 2023 e 2024 - Atividades
e Planos" (infográfico/slide, sem texto tabular extraível de forma genérica — os
números e listas de municípios abaixo foram conferidos linha a linha contra o PDF
original). Mesma abordagem de "casos especiais" já usada em lib/pdf_parser.py para
os boletins do TSE: PDFs de layout gráfico não dão para parsear de forma robusta e
genérica, então os fatos são transcritos como dados.
"""

# (categoria, indicador, ano, valor, unidade)
INDICADORES_ESTADO = [
    ("Orçamento", "Execução orçamentária do exercício", 2023, 96.80, "%"),
    ("Orçamento", "Recursos do Tesouro Estadual sobre o total de fontes", 2023, 98.66, "%"),
    ("Orçamento", "Outras fontes de financiamento sobre o total", 2023, 1.34, "%"),
    ("Orçamento", "Orçamento total aprovado (LOA)", 2024, 995860051, "R$"),
    ("Orçamento", "Despesa com Pessoal e Encargos Sociais sobre o orçamento", 2024, 66.36, "%"),
    ("Orçamento", "Outras Despesas Correntes sobre o orçamento", 2024, 27.57, "%"),
    ("Orçamento", "Recursos do Tesouro Estadual sobre o total de fontes", 2024, 98.90, "%"),

    ("Gestão Fiscal", "Despesa de Pessoal sobre a Receita Corrente Líquida (RCL)", 2023, 1.4366, "%"),
    ("Gestão Fiscal", "Limite de alerta da RCL (Lei de Responsabilidade Fiscal)", 2023, 1.80, "%"),

    ("Estrutura Física", "Municípios com Promotoria de Justiça instalada (Capital + interior)", 2024, 119, "municípios"),
    ("Estrutura Física", "Municípios sem Promotoria de Justiça instalada", 2024, 25, "municípios"),
    ("Estrutura Física", "Instalações próprias", 2024, 42, "unidades"),
    ("Estrutura Física", "Instalações locadas", 2024, 19, "unidades"),
    ("Estrutura Física", "Instalações cedidas", 2024, 3, "unidades"),
    ("Estrutura Física", "Instalações em sala de fórum", 2024, 55, "unidades"),

    ("Pessoal", "Membros ativos", 2023, 322, "pessoas"),
    ("Pessoal", "Servidores ativos", 2023, 1267, "pessoas"),
    ("Pessoal", "Estagiários ativos", 2023, 834, "pessoas"),
    ("Pessoal", "Total de integrantes ativos", 2023, 2423, "pessoas"),
    ("Pessoal", "Servidores nomeados no ano", 2023, 155, "pessoas"),
    ("Pessoal", "Membros (Promotores de Justiça) nomeados", 2024, 65, "pessoas"),
    ("Pessoal", "Cargos de Promotor vagos e não instalados", 2024, 233, "cargos"),
    ("Pessoal", "Novos cargos de servidores previstos (PCCR institucional)", 2024, 495, "cargos"),
    ("Pessoal", "Assessores ministeriais de área finalística (ingresso previsto)", 2024, 90, "pessoas"),
    ("Pessoal", "Estagiários de pós-graduação (ingresso previsto)", 2024, 150, "pessoas"),

    ("Tecnologia da Informação", "Implantação do sistema SAJ MPPA nas Promotorias de Justiça", 2023, 95, "%"),
    ("Tecnologia da Informação", "Promotorias de Justiça com SAJ MPPA implantado", 2023, 80, "unidades"),

    ("Obras e Infraestrutura", "Municípios atendidos com projetos, obras e reformas", 2023, 39, "municípios"),
    ("Obras e Infraestrutura", "Novas sedes planejadas", 2024, 12, "municípios"),
    ("Obras e Infraestrutura", "Outras obras e reformas planejadas", 2024, 28, "municípios"),
]

# Municípios paraenses SEM Promotoria de Justiça instalada (situação vigente conforme o
# relatório). O texto entre parênteses no PDF ("termo de X") indica a comarca/termo
# judiciário ao qual o município está vinculado — removido para casar com o nome oficial.
MUNICIPIOS_SEM_PROMOTORIA = [
    "Terra Alta", "São João da Ponta", "Cachoeira do Piriá", "Nova Esperança do Piriá",
    "Quatipuru", "Tracuateua", "Santa Cruz do Arari", "Abel Figueiredo",
    "Bom Jesus do Tocantins", "Brejo Grande do Araguaia", "Nova Ipixuna",
    "Palestina do Pará", "Piçarra", "Água Azul do Norte", "Bannach", "Cumaru do Norte",
    "Floresta do Araguaia", "Pau D'arco", "Santa Maria das Barreiras", "Sapucaia",
    "Placas", "Trairão", "Belterra", "Curuá", "Mojuí dos Campos",
]

# Alias local só para os dados do MPPA: nomes citados no PDF que não são município
# oficial do IBGE, mas sim distrito/bairro de outro município.
MPPA_ALIAS_MUNICIPIO = {
    "MOSQUEIRO": "BELEM",  # Ilha de Mosqueiro é distrito de Belém, não município próprio
}

# (tipo, ano, [municípios])
OBRAS = [
    ("Projetos, obras e reformas", 2023, [
        "Abaetetuba", "Acará", "Ananindeua", "Augusto Corrêa", "Barcarena", "Belém",
        "Benevides", "Breves", "Canaã dos Carajás", "Curionópolis", "Cametá", "Capanema",
        "Faro", "Garrafão do Norte", "Inhangapi", "Mãe do Rio", "Marabá", "Marituba",
        "Monte Alegre", "Moju", "Maracanã", "Muaná", "Ourém", "Oriximiná", "Parauapebas",
        "Paragominas", "Redenção", "Rondon do Pará", "Santa Izabel do Pará",
        "São Domingos do Araguaia", "Santarém", "Salvaterra", "Santarém Novo",
        "Tailândia", "Tomé-Açu", "Tucuruí", "Xinguara", "Viseu",
    ]),
    ("Inauguração de nova sede", 2023, ["Canaã dos Carajás", "Moju"]),
    ("Adaptação de RO para sede de PJ", 2023, [
        "Oriximiná", "Mãe do Rio", "Curionópolis", "Muaná", "Barcarena",
    ]),
    ("Construção de sede em andamento", 2023, [
        "Tomé-Açu", "Barcarena", "Cametá", "Capanema", "Monte Alegre", "Redenção",
    ]),
    ("Terreno doado para construção de PJ", 2023, ["Breves", "Capanema", "Paragominas"]),
    ("Licitação iniciada para nova sede", 2023, [
        "Ourilândia do Norte", "Abaetetuba", "Salvaterra",
    ]),
    ("Construção de nova sede (planejada)", 2024, [
        "Bragança", "Mosqueiro", "Benevides", "Breves", "Capanema", "Itaituba",
        "Jacareacanga", "Paragominas", "Prainha", "Santa Izabel do Pará",
        "São João do Araguaia", "Tucuruí",
    ]),
    ("Obra/reforma (programada)", 2024, [
        "Curuçá", "Belém", "Ananindeua", "Ourilândia do Norte", "Augusto Corrêa",
        "Novo Progresso", "Rurópolis", "Marapanim", "Portel", "Marabá", "Redenção",
        "Santarém", "Altamira", "Castanhal", "Rio Maria", "Conceição do Araguaia",
        "Marituba", "Óbidos", "São Félix do Xingu", "Santa Izabel do Pará",
        "São Miguel do Guamá", "Abaetetuba", "Barcarena", "Tomé-Açu",
        "Limoeiro do Ajuru", "Cametá", "Canaã dos Carajás",
    ]),
    ("Adaptação de RO para PJ", 2024, ["Augusto Corrêa", "Portel"]),
]

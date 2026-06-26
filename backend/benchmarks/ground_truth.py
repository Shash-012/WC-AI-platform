"""
benchmarks/ground_truth.py

Labeled evaluation set for the World Cup RAG pipeline.

Each entry has:
  query             - the question to run through the retriever
  relevant_keywords - any one of these strings appearing (case-insensitive)
                      in a retrieved document's page_content counts as a hit
  description       - human-readable label for reporting

Queries span all four data files: teams.txt, players.txt, groups.txt, fixtures.txt.
"""

GROUND_TRUTH = [
    # ── Teams ──────────────────────────────────────────────────────────────
    {
        "query": "Who manages Argentina and what formation do they use?",
        "relevant_keywords": ["scaloni", "lionel scaloni"],
        "description": "Argentina manager",
    },
    {
        "query": "What is Spain's tactical style?",
        "relevant_keywords": ["de la fuente", "possession", "rodri", "lamine yamal"],
        "description": "Spain tactics",
    },
    {
        "query": "Which team uses a Gegenpressing 4-2-3-1 system?",
        "relevant_keywords": ["rangnick", "austria", "gegenpressing"],
        "description": "Austria Gegenpressing style",
    },
    {
        "query": "Who is the key player for Norway and what is their formation?",
        "relevant_keywords": ["haaland", "solbakken", "norway"],
        "description": "Norway key player",
    },
    {
        "query": "Which team does Carlo Ancelotti manage at the World Cup?",
        "relevant_keywords": ["brazil", "ancelotti"],
        "description": "Brazil manager",
    },
    {
        "query": "What formation does Morocco use and who are their key players?",
        "relevant_keywords": ["hakimi", "en-nesyri", "ouahbi", "morocco"],
        "description": "Morocco formation",
    },
    {
        "query": "Who manages France and what is their tactical approach?",
        "relevant_keywords": ["deschamps", "france", "mbappé", "mbappe"],
        "description": "France manager",
    },

    # ── Players ────────────────────────────────────────────────────────────
    {
        "query": "Who holds the record for the most Ballon d'Or awards?",
        "relevant_keywords": ["messi", "ballon d'or"],
        "description": "Ballon d'Or record",
    },
    {
        "query": "Who is the all-time leading international goalscorer in football?",
        "relevant_keywords": ["cristiano ronaldo", "ronaldo", "al-nassr"],
        "description": "All-time international goalscorer",
    },
    {
        "query": "Which player holds the record for most goals in a single Premier League season?",
        "relevant_keywords": ["haaland", "premier league season"],
        "description": "Premier League season goals record",
    },
    {
        "query": "Who is injured and expected to miss the start of the 2026 World Cup?",
        "relevant_keywords": ["neymar", "injured", "miss", "barcola", "hakimi"],
        "description": "Injured players",
    },
    {
        "query": "Who was the top scorer at the 2023 AFC Asian Cup?",
        "relevant_keywords": ["aymen hussein", "hussein", "iraq"],
        "description": "AFC Asian Cup top scorer",
    },
    {
        "query": "Who scored the winning goal against Argentina at the 2022 World Cup?",
        "relevant_keywords": ["salem al-dawsari", "al-dawsari", "saudi arabia"],
        "description": "Saudi Arabia upset goal",
    },
    {
        "query": "Who is the fastest player in football?",
        "relevant_keywords": ["alphonso davies", "davies", "fastest"],
        "description": "Fastest player",
    },
    {
        "query": "Who is the all-time top scorer for Ecuador?",
        "relevant_keywords": ["enner valencia", "valencia", "ecuador"],
        "description": "Ecuador all-time top scorer",
    },

    # ── Groups ─────────────────────────────────────────────────────────────
    {
        "query": "Which teams are in Group C of the 2026 World Cup?",
        "relevant_keywords": ["brazil", "morocco", "haiti", "scotland"],
        "description": "Group C composition",
    },
    {
        "query": "Which group do Canada play in and who are their opponents?",
        "relevant_keywords": ["group b", "bosnia", "qatar", "switzerland"],
        "description": "Canada group",
    },
    {
        "query": "Where does the United States play their opening match?",
        "relevant_keywords": ["sofi stadium", "los angeles", "paraguay"],
        "description": "USA opening match venue",
    },
    {
        "query": "Which group features Germany and Ivory Coast?",
        "relevant_keywords": ["group e", "germany", "ivory coast", "ecuador", "curaçao"],
        "description": "Group E composition",
    },

    # ── Fixtures ───────────────────────────────────────────────────────────
    {
        "query": "When and where do Brazil play Morocco?",
        "relevant_keywords": ["june 13", "metlife", "new jersey"],
        "description": "Brazil vs Morocco fixture",
    },
    {
        "query": "Where does England play their opening match?",
        "relevant_keywords": ["at&t stadium", "dallas", "june 17", "croatia"],
        "description": "England opening fixture",
    },
    {
        "query": "When does Spain play their first match and against who?",
        "relevant_keywords": ["june 15", "mercedes-benz", "atlanta", "cape verde"],
        "description": "Spain opening fixture",
    },
    {
        "query": "Where does the tournament opening match take place?",
        "relevant_keywords": ["estadio azteca", "mexico city", "mexico", "south africa"],
        "description": "Tournament opening match",
    },
]

# Cassotis Optimization — Teoria da Decisão UFMG 2026/2

Projeto da disciplina **Teoria da Decisão** para o case **Otimização do Custo e Qualidade de Pilhas de Minério**.

O objetivo é desenvolver, documentar e avaliar uma solução baseada em VNS/GVNS para as etapas mono-objetivo e multiobjetivo e, posteriormente, aplicar métodos de apoio multicritério à decisão.

## Estado atual

Entrega 1 (mono-objetivo): formulação, representação, heurística construtiva, vizinhanças N1/N2/N3, perturbações P1/P2/P3, tratamento de inviabilidade, GVNS e script de experimentos implementados. Os resultados finais ainda não foram gerados: faltam calibrar os parâmetros experimentais, congelar a configuração e escolher as seeds finais (D017).

Consolidados:

- variável de decisão em número de caminhões (2 kt cada);
- disponibilidade mínima e máxima global por minério, considerando as 10 pilhas;
- representação por posições de caminhão, que preserva massa;
- elegibilidade preservada pelos operadores de vizinhança;
- FeT mantido no domínio, mas não ativo como restrição na instância de exemplo;
- N3: realocação com substituição em cadeia (D008);
- heurística construtiva sugerida no enunciado (D013);
- tratamento de inviabilidade: regra de viabilidade (D007);
- GVNS com VND N1 → N2 → N3, primeira melhoria (D009, D014);
- SHAKE com estruturas próprias P1, P2, P3 (D015);
- aceitação por melhoria estrita (D016);
- parada por número de avaliações (D010);
- separação entre seeds de calibração e seeds finais (D017).

Ainda experimentais: orçamento (200 mil avaliações), tamanho da amostra de N2/N3 (500), tamanhos de P1/P2/P3 e as seeds finais.

As decisões da GVNS estão explicadas em linguagem direta em [`docs/gvns_decisoes.md`](docs/gvns_decisoes.md). O registro formal está em [`docs/decision_log.md`](docs/decision_log.md).

Pendentes: resultados finais da Entrega 1, Entrega 2 (multiobjetivo), Entrega 3 (decisão multicritério e Streamlit), relatório e apresentações.

## Fonte do problema

A especificação principal é o enunciado do case da disciplina. Os dados em `data/example_instance/` correspondem ao **exemplo apresentado no anexo do enunciado** e não devem ser confundidos com uma eventual instância definitiva fornecida posteriormente.

Há também uma clarificação da professora sobre disponibilidade: os limites mínimo e máximo de cada minério são globais sobre todas as pilhas. Se um minério tiver disponibilidade mínima 3, devem ser utilizados pelo menos 3 caminhões desse minério no total, distribuídos livremente entre as 10 pilhas, respeitando as demais restrições.

## Estrutura

```text
.
├── data/example_instance/        # instância do anexo do enunciado (CSV)
├── docs/
│   ├── decision_log.md           # registro formal das decisões
│   ├── gvns_decisoes.md          # explicação das decisões da GVNS
│   ├── problem_formulation.md
│   ├── feasibility_strategy.md
│   ├── experiment_protocol.md
│   ├── deliverables_checklist.md
│   └── source_notes.md
├── src/cassotis_optimization/
│   ├── domain.py, io.py, validation.py, solution.py
│   ├── evaluator.py              # núcleo único: custo, qualidade, violações
│   ├── objectives.py             # seleção de f1/f2/f3
│   ├── feasibility.py            # violação normalizada e regra de viabilidade
│   ├── visualization.py          # figuras (convergência, solução)
│   └── algorithms/
│       ├── constructive.py       # heurística construtiva
│       ├── vizinhancas.py        # N1, N2, N3 (enumeração e amostragem uniforme)
│       ├── perturbacoes.py       # P1, P2, P3 (SHAKE)
│       └── gvns.py               # GVNS + VND
├── scripts/
│   ├── validate_instance.py
│   └── run_mono_experiments.py   # 5 execuções × f1/f2/f3, tabelas e figuras
├── tests/
├── app/                          # Streamlit (Entrega 3)
├── notebooks/
└── results/                      # saídas geradas pelos scripts
```

## Preparação do ambiente

Requer Python 3.11 ou superior.

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,app]"
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,app]"
```

## Validação inicial

```bash
python scripts/validate_instance.py
pytest
```

## Experimentos da Entrega 1

```bash
python scripts/run_mono_experiments.py --seeds S1 S2 S3 S4 S5
```

As seeds são obrigatórias. As seeds finais serão registradas em D017 antes da rodada oficial. Para um teste rápido:

```bash
python scripts/run_mono_experiments.py --seeds 1 2 --budget 5000 --out results/teste
```

O script gera, na pasta de saída (padrão `results/mono/`):

- o JSON de cada execução;
- `summary.csv` e `summary.md` (mín/std/máx);
- as curvas de convergência;
- a figura da melhor solução de cada objetivo.

Parâmetros: `--seeds`, `--budget`, `--objectives`, `--out`.

## Regra de desenvolvimento

Nenhuma decisão de modelagem ou algoritmo deve ser alterada silenciosamente. Mudanças relevantes devem ser registradas em `docs/decision_log.md` com motivação, alternativas consideradas e impacto esperado.

A lógica central deve permanecer em `src/`. Notebooks e Streamlit devem consumir essa implementação, e não recriar fórmulas ou regras paralelas.

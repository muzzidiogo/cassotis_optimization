# Decision Log

Este documento registra decisões relevantes do projeto. Não deve ser usado apenas para descrever o que foi implementado; deve registrar **por que** cada escolha foi feita.

Estados possíveis: `CONFIRMADA`, `CONSOLIDADA`, `PENDENTE`, `SUPERADA`.

---

## D001 — Unidade da variável de decisão

**Status:** CONSOLIDADA

**Decisão:** representar \(x_{ip}\) como número de caminhões do minério \(i\) usados na pilha \(p\).

**Alternativa considerada:** representar diretamente massa em kt.

**Motivação:** cada caminhão possui 2 kt e as disponibilidades do enunciado já são dadas em caminhões. A escolha incorpora naturalmente a integralidade e evita uma restrição adicional de múltiplos de 2 kt.

**Impacto:** massa em kt é calculada como \(2x_{ip}\).

---

## D002 — Interpretação de disponibilidade mínima e máxima

**Status:** CONFIRMADA

**Decisão:** os limites são globais sobre as 10 pilhas:

\[
d_i^{min}\le\sum_p x_{ip}\le d_i^{max}.
\]

**Fonte:** esclarecimento explícito da professora. Se um minério tem mínimo 3, pelo menos 3 caminhões desse minério devem ser utilizados no total; eles podem ser concentrados em uma pilha ou distribuídos entre várias.

**Impacto:** disponibilidade não deve ser verificada separadamente por pilha.

---

## D003 — Representação computacional por slots de caminhão

**Status:** CONSOLIDADA

**Decisão:** representar cada pilha por um vetor com \(M_p/2\) posições; cada posição contém um minério e representa um caminhão.

**Alternativa considerada:** armazenar apenas a matriz de contagens \(x_{ip}\).

**Motivação:** o enunciado define N1 e N2 em termos de posições no vetor de composição. A representação por slots torna os movimentos naturais e preserva massa.

**Impacto:** a matriz \(x_{ip}\) continua útil, mas é derivada da solução.

---

## D004 — Tratamento da massa

**Status:** CONSOLIDADA

**Decisão:** preservar massa por construção mantendo fixo o tamanho do vetor de cada pilha.

**Motivação:** não há benefício em explorar estados com massa incorreta quando a representação pode eliminar essa classe de inviabilidade sem reduzir a expressividade da solução.

---

## D005 — Elegibilidade logística

**Status:** CONSOLIDADA

**Decisão:** N1, N2 e futuras vizinhanças devem impedir inserção de minério em grupo para o qual ele não seja elegível sempre que isso puder ser garantido diretamente pelo operador.

**Motivação:** elegibilidade é uma condição discreta simples e pode ser preservada sem introduzir trade-off útil.

---

## D006 — FeT

**Status:** CONSOLIDADA

**Decisão:** manter FeT nos dados, cálculos e visualizações, mas não tratá-lo como restrição ativa na instância de exemplo.

**Motivação:** o enunciado informa limites 0%–100% e declara que FeT não influencia a otimização neste case.

---

## D007 — Política de tratamento de inviabilidade de qualidade e disponibilidade

**Status:** CONSOLIDADA

**Escopo:** violações de SiO2, Al2O3 e disponibilidade global.

**Decisão:** regra de viabilidade (dominação por restrições), implementada em `feasibility.feasibility_rule_key` e usada em toda comparação da GVNS:

1. solução viável vence solução inviável;
2. entre viáveis, vence a de menor objetivo;
3. entre inviáveis, vence a de menor \(V(X)\) normalizado (`normalized_violation`); o objetivo desempata.

**Alternativas consideradas:** rejeição pura; penalização \(f+\lambda V\) estática ou dinâmica; reparo; operadores totalmente preservadores; estratégia em duas fases.

**Motivação:**

- a solução inicial da construtiva é inviável (SiO2 ≈ 7,1% nas pilhas do Sinter 1, limite 6,2%), o que descarta a rejeição pura;
- não há coeficiente \(\lambda\) para calibrar, o que evita três calibrações dependentes da escala (custo ~10^7 R$ contra desvios ~1);
- a regra não depende da escala do objetivo, então pode ser reutilizada nas escalarizações da Entrega 2;
- equivale a uma estratégia em duas fases (primeiro reduzir \(V\), depois otimizar \(f\)) sem precisar de uma troca explícita de fase.

**Consequências:** depois de viável, a solução corrente não volta a ser inviável, e a travessia de regiões inviáveis fica limitada (Aula 04, slide 14). A perturbação pode gerar soluções inviáveis, que a VND usa como ponto de partida. \(V(X)\) permanece a soma linear das violações normalizadas (não a soma de quadrados da Aula 04), porque só é usado para ordenar soluções inviáveis entre si.

**Evidência:** ainda não há evidência experimental da configuração consolidada. Ela será produzida na calibração e nas execuções finais (D017).

Ver `docs/feasibility_strategy.md` e `docs/gvns_decisoes.md`.

---

## D008 — Terceira vizinhança N3

**Status:** CONSOLIDADA

**Decisão:** utilizar uma vizinhança de realocação com substituição em cadeia.

O movimento seleciona duas pilhas distintas \(p_a\) e \(p_b\), contendo respectivamente os minérios \(m_x\) e \(m_y\), e um novo minério \(m_z\). O movimento realiza:

\[
p_a: m_x \rightarrow m_z
\]

\[
p_b: m_y \rightarrow m_x
\]

desde que \(m_z\) seja elegível para \(p_a\) e \(m_x\) seja elegível para \(p_b\).

**Alternativas consideradas:** ciclo entre três pilhas, dupla substituição dentro de uma pilha e movimentos guiados diretamente pela medida de inviabilidade \(V(X)\).

**Motivação:** N3 combina, em uma única transição, duas características que aparecem separadamente em N1 e N2: alteração da composição global de minérios e realocação entre pilhas. O movimento pode modificar diretamente \(f_1\), \(f_2\) e \(f_3\), sendo também adequado para reutilização nas etapas multiobjetivo.

A execução coordenada evita depender da aceitação de estados intermediários que seriam necessários ao decompor o movimento em aplicações sucessivas de outras vizinhanças.

**Impacto:** a massa das pilhas e a elegibilidade são preservadas por construção. O consumo global de \(m_x\) permanece inalterado, enquanto o consumo de \(m_y\) diminui em uma unidade e o de \(m_z\) aumenta em uma unidade. Portanto, o movimento pode gerar violações de disponibilidade e qualidade, que deverão ser tratadas pela política definida em D007.

O movimento pode alterar o custo segundo:

\[
\Delta f_1 = 2000(c_z-c_y).
\]

**Implementação:** `algorithms/vizinhancas.py` (`n3_moves`, `sample_n3_move`, `n3_relocate_replace`). Os movimentos são definidos sobre os minérios distintos de cada pilha (ver D014).

---

## D009 — VNS ou GVNS

**Status:** CONSOLIDADA

**Decisão:** GVNS (Aula 02, slides 36–38): perturbação P_k seguida de VND sobre N1 → N2 → N3, com troca de vizinhança "melhorou → volta para k=1 / ℓ=1; senão → próxima".

**Alternativas consideradas:** VNS básica com uma única vizinhança de refinamento; RVNS.

**Motivação:** o enunciado exige três vizinhanças. Na GVNS as três participam da busca local, e a perturbação tem estruturas próprias (D015). As vizinhanças são complementares: N1 altera o consumo global, N2 só redistribui entre pilhas, N3 faz as duas coisas.

**Implementação:** `algorithms/gvns.py`.

---

## D010 — Critério de parada e orçamento experimental

**Status:** CONSOLIDADA (critério); PENDENTE (valor do orçamento)

**Decisão:** o critério de parada é o número de avaliações de soluções candidatas por execução, igual para f1, f2 e f3, sem critério auxiliar. O tempo é registrado como informação complementar.

O valor padrão é `GVNSConfig.max_evaluations = 200_000`, configurável por `--budget`. Esse número ainda não foi definido experimentalmente e deve ser revisto antes de congelar a configuração.

**Alternativas consideradas:** tempo de parede; número de iterações da GVNS; iterações sem melhoria.

**Motivação:** o número de avaliações não depende da máquina, coincide com o eixo x das curvas de convergência e permite comparação justa entre objetivos.

---

## D011 — Reprodutibilidade

**Status:** CONSOLIDADA

**Decisão:** separar fase de calibração de parâmetros da fase de resultados finais e registrar seeds/configurações das execuções finais.

**Motivação:** evitar seleção oportunista de configurações após observar os resultados e permitir reprodução do relatório.
---

## D012 — Separação entre avaliação e objetivo ativo

**Status:** CONSOLIDADA

**Decisão:** a função `evaluate()` calcula simultaneamente \(f_1\), \(f_2\), \(f_3\), qualidade e violações. A função `objective_value()` apenas seleciona qual objetivo será minimizado em uma execução mono-objetivo.

**Motivação:** evitar duplicação de cálculos e desacoplar a definição do problema da metaheurística.

**Impacto:** o mesmo algoritmo poderá ser reutilizado para otimizar \(f_1\), \(f_2\) ou \(f_3\), e a mesma avaliação poderá ser reaproveitada nas etapas multiobjetivo.

---

## D013 — Heurística construtiva

**Status:** CONSOLIDADA

**Decisão:** a solução inicial é construída em duas fases. Primeiro, são atendidas as disponibilidades mínimas globais dos minérios, distribuindo esses caminhões apenas em pilhas elegíveis. Depois, os slots restantes são preenchidos com os minérios elegíveis de menor custo que ainda possuam disponibilidade máxima restante.

**Alternativas consideradas:** não foram comparadas outras construtivas.

**Motivação:** segue a sugestão do enunciado e garante, já na construção, massa correta, elegibilidade e limites globais de disponibilidade. A escolha não se apoia em comparação empírica com outras construtivas, e não se afirma que ela seja superior a elas.

**Consequências:** a solução inicial pode ser inviável quanto aos limites de SiO₂ e Al₂O₃, e isso é tratado pela regra de D007. A construtiva é determinística, então todas as execuções partem da mesma solução.

**Observação:** na instância de exemplo, a solução construída tem custo R$ 59,34 mi, f2 = 14,90 e f3 = 7,00. Ela é inviável em SiO2 nas pilhas do Sinter 1 (≈ 7,1%) e levemente em Al2O3 em P1, P2 e P4.

---

## D014 — Busca local: primeira melhoria e VND N1 → N2 → N3

**Status:** CONSOLIDADA (estrutura); PENDENTE (tamanho da amostra)

**Decisão:**

- busca local de primeira melhoria, repetida até que uma passada não encontre movimento de melhoria, com a vizinhança percorrida em ordem aleatória definida pela semente;
- VND na ordem N1 → N2 → N3, da vizinhança menor para a maior;
- movimentos definidos sobre os minérios distintos de cada pilha, porque posições com o mesmo minério geram a mesma solução. O conjunto de soluções alcançáveis é o mesmo das definições do enunciado (por posição);
- N1 (cerca de 1.100 movimentos distintos) é explorada por completo, então o resultado da busca em N1 é um ótimo local de N1;
- N2 (cerca de 3.000 movimentos) e N3 (cerca de 10^5) são exploradas por amostra. Em cada passada, sorteiam-se até `sample_size` movimentos **distintos**, uniformemente e sem reposição sobre o espaço de movimentos distintos (`vizinhancas.sample_moves`):
  - N2: a vizinhança é enumerada e sorteada sem reposição;
  - N3: os movimentos são agrupados por prefixo (pilha a, pilha b, m_x, m_y). Cada prefixo é sorteado com peso igual ao número de m_z válidos e depois m_z é sorteado uniformemente, o que dá probabilidade igual a cada movimento distinto sem enumerar a vizinhança. Repetições são descartadas até completar a amostra;
- quando N2 ou N3 terminam sem melhoria, isso significa apenas que nenhum movimento da última amostra melhorou, e não que a solução é um ótimo local dessas vizinhanças.

`sample_size = 500` é um valor padrão experimental, configurável em `GVNSConfig`.

**Alternativas consideradas:** melhor melhoria; exploração completa de N2; sorteio por posição (slot), usado na primeira versão.

**Motivação:** melhor melhoria e exploração completa de N3 consumiriam o orçamento em poucos passos. O sorteio por posição dava mais chance aos minérios que ocupam mais posições de uma pilha e podia avaliar o mesmo movimento várias vezes na mesma passada. Por isso foi substituído pelo sorteio uniforme sem repetição.

**Evidência:** a calibração feita com a primeira versão (sorteio por posição e SHAKE antigo) não vale para a configuração atual e foi descartada. O tamanho da amostra será recalibrado com seeds de calibração novas (D017).

---

## D015 — Perturbação (SHAKE) com estruturas próprias P1, P2, P3

**Status:** CONSOLIDADA (estrutura); PENDENTE (parâmetros)

**Decisão:** a GVNS tem dois níveis separados:

- N1, N2 e N3 são usadas só pela VND, para intensificação;
- o SHAKE usa estruturas próprias, de intensidade crescente (`algorithms/perturbacoes.py`), com k_max = 3.

As estruturas são:

- **P1 — perturbação pequena:** troca o minério de `p1_positions = 2` posições sorteadas por outro minério elegível;
- **P2 — movimentos encadeados:** cadeia de ejeção em `p2_chain_length = 3` pilhas distintas. A primeira pilha recebe um minério novo, cada pilha seguinte recebe o minério que saiu da anterior, e o minério da última pilha sai da solução. A elegibilidade é exigida em cada elo;
- **P3 — perturbação forte:** permutação cíclica de uma posição de cada uma de `p3_piles = 5` pilhas do mesmo grupo de sinter. Pilhas do mesmo grupo têm a mesma elegibilidade, então qualquer minério pode circular entre elas. O consumo global não muda; a qualidade de até 5 pilhas muda de uma vez.

As perturbações sorteiam posições (caminhões) uniformemente, seguindo o enunciado. Isso é intencional: é um sorteio de caminhão, e não uma exploração de vizinhança.

A solução perturbada é avaliada (conta no orçamento) e passada à VND.

**Alternativas consideradas:** k × 3 movimentos aleatórios de N1, N2 e N3 (primeira versão, que misturava as vizinhanças da VND com a intensidade da perturbação); reconstrução parcial de pilhas.

**Motivação:** separar intensificação (N_ℓ) de diversificação (P_k), como no pseudocódigo da GVNS da Aula 02. Quando a VND não melhora, o SHAKE passa progressivamente para regiões mais distantes: P1 altera 2 caminhões, P2 até 3 pilhas em cadeia, P3 até 5 pilhas.

**Consequências:** P1 e P2 podem violar a disponibilidade; P3 não. As violações são tratadas por D007.

**Evidência:** pendente. Os valores 2, 3 e 5 são padrões experimentais, configuráveis em `GVNSConfig`.

---

## D016 — Critério de aceitação

**Status:** CONSOLIDADA

**Decisão:** X'' substitui X somente se for estritamente melhor pela regra de D007, com tolerância relativa de 10^-12 para ignorar ruído de ponto flutuante.

**Alternativas consideradas:** aceitar soluções iguais (movimento lateral); aceitação probabilística do tipo recozimento simulado.

**Motivação:** é a aceitação do pseudocódigo da GVNS visto em aula e não introduz parâmetros. A diversificação vem do SHAKE.

---

## D017 — Sementes e separação entre calibração e resultados finais

**Status:** CONSOLIDADA (separação); PENDENTE (seeds finais)

**Decisão:**

- calibração e resultados finais usam conjuntos de seeds disjuntos;
- as 5 seeds finais serão escolhidas e registradas aqui **depois** de congelar o algoritmo e os parâmetros, e **antes** de gerar os resultados finais;
- elas devem ser diferentes de todas as seeds já usadas:
  - 1–5 (rodada descartada, feita com a primeira versão);
  - 1001–1003 (calibração da primeira versão);
  - 2001 (verificação da versão atual);
  - as dos testes automatizados (0, 1, 3, 5, 7, 11, 13, 17, 21 e 42);
- os resultados finais entram num commit ou PR separado da implementação;
- o desvio-padrão reportado é o amostral (n−1). A construtiva é determinística, então as execuções diferem apenas pela seed da GVNS.

`scripts/run_mono_experiments.py` exige `--seeds` e não tem seeds padrão, para evitar que resultados finais sejam gerados sem querer.

**Motivação:** aplicar D011. As seeds 1–5 já tiveram os resultados observados, então não podem ser as seeds finais.

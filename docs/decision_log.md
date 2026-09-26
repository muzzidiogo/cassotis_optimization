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

**Status:** PENDENTE

**Escopo:** violações de SiO2, Al2O3 e disponibilidade global.

**Alternativas em estudo:**

- rejeição após obtenção de solução factível;
- penalização;
- reparo;
- operadores totalmente preservadores;
- regra de viabilidade/dominação por restrições;
- estratégia em duas fases: busca de factibilidade e depois otimização factível.

**Critérios para decisão:** simplicidade, independência da escala dos objetivos, capacidade de encontrar região factível, possibilidade de escapar de ótimos locais, custo computacional e estabilidade para reutilização na Entrega 2.

Ver `docs/feasibility_strategy.md`.

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

A implementação da vizinhança permanece pendente.

---

## D009 — VNS ou GVNS

**Status:** PENDENTE

A decisão deverá considerar a organização desejada para busca local, perturbação e exploração das três vizinhanças.

---

## D010 — Critério de parada e orçamento experimental

**Status:** PENDENTE

O protocolo final deve permitir comparação justa entre objetivos e configurações. Número de avaliações de solução é candidato preferencial para orçamento principal; tempo pode ser reportado como métrica complementar.

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

## D013 — Heurística construtiva baseline

**Status:** EXPERIMENTAL

**Decisão:** a solução inicial é construída em duas fases. Primeiro, são atendidas as disponibilidades mínimas globais dos minérios, distribuindo esses caminhões apenas em pilhas elegíveis. Depois, os slots restantes são preenchidos com os minérios elegíveis de menor custo que ainda possuam disponibilidade máxima restante.

**Motivação:** seguir a lógica sugerida no enunciado e garantir, já na construção, massa correta, elegibilidade e limites globais de disponibilidade.

**Impacto:** a solução inicial pode continuar inviável quanto aos limites de SiO₂ e Al₂O₃. A política de tratamento dessas inviabilidades permanece pendente em D007.
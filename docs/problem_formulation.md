# Formulação do problema

## 1. Escopo

A usina possui dois equipamentos de sinterização. Cada equipamento é alimentado por cinco pilhas. Deve-se definir quanto de cada minério compõe cada pilha de forma a:

1. atingir exatamente a massa de cada pilha;
2. respeitar elegibilidade logística dos minérios;
3. respeitar disponibilidade mínima e máxima global de cada minério;
4. respeitar limites de SiO2 e Al2O3;
5. minimizar, separadamente na Entrega 1:
   - custo total;
   - soma dos desvios quadráticos de SiO2 em relação ao alvo;
   - soma dos desvios quadráticos de Al2O3 em relação ao alvo.

Cada caminhão transporta 2 kt.

## 2. Conjuntos e índices

- \(I\): conjunto de minérios, índice \(i\).
- \(P\): conjunto de pilhas, índice \(p\).
- \(G=\{1,2\}\): grupos/equipamentos de sinterização, índice \(g\).
- \(g(p)\): grupo ao qual a pilha \(p\) pertence.

## 3. Parâmetros

- \(q=2\): capacidade de um caminhão em kt.
- \(M_p\): massa final requerida da pilha \(p\), em kt.
- \(n_p=M_p/q\): número de caminhões da pilha \(p\).
- \(c_i\): preço do minério \(i\), em R$/t.
- \(s_i\): teor de SiO2 do minério \(i\), em %.
- \(a_i\): teor de Al2O3 do minério \(i\), em %.
- \(f_i\): teor de FeT do minério \(i\), em %.
- \(d_i^{min}\), \(d_i^{max}\): disponibilidade mínima e máxima global do minério \(i\), em caminhões.
- \(e_{ig}\in\{0,1\}\): elegibilidade do minério \(i\) para o grupo \(g\).
- \(L_g^{Si}\), \(U_g^{Si}\), \(T_g^{Si}\): limite inferior, superior e alvo de SiO2.
- \(L_g^{Al}\), \(U_g^{Al}\), \(T_g^{Al}\): limite inferior, superior e alvo de Al2O3.

## 4. Variável de decisão

\[
x_{ip} \in \mathbb{Z}_{\ge 0}
\]

é o número de caminhões do minério \(i\) destinados à pilha \(p\).

A escolha por número de caminhões incorpora diretamente a integralidade física. A massa correspondente é \(2x_{ip}\) kt.

## 5. Restrições

### 5.1 Massa exata

\[
\sum_{i\in I} x_{ip} = n_p
\qquad \forall p\in P.
\]

### 5.2 Elegibilidade

\[
x_{ip}=0
\qquad
\text{quando } e_{i,g(p)}=0.
\]

### 5.3 Disponibilidade global

Conforme esclarecimento da professora:

\[
d_i^{min}
\le
\sum_{p\in P} x_{ip}
\le
d_i^{max}
\qquad \forall i\in I.
\]

A disponibilidade não é por pilha. Um mínimo 3 significa utilizar pelo menos três caminhões daquele minério no total das 10 pilhas.

### 5.4 Qualidade

Como todos os caminhões têm a mesma massa:

\[
S_p =
\frac{1}{n_p}
\sum_{i\in I} s_i x_{ip}
\]

e

\[
A_p =
\frac{1}{n_p}
\sum_{i\in I} a_i x_{ip}.
\]

As restrições são:

\[
L_{g(p)}^{Si}
\le
S_p
\le
U_{g(p)}^{Si}
\qquad \forall p
\]

e

\[
L_{g(p)}^{Al}
\le
A_p
\le
U_{g(p)}^{Al}
\qquad \forall p.
\]

FeT deve permanecer disponível para cálculo e visualização, mas os limites 0% e 100% tornam sua restrição inativa na instância de exemplo.

## 6. Funções objetivo

### \(f_1\): custo total

Como 2 kt = 2000 t:

\[
f_1(X)
=
2000
\sum_{p\in P}
\sum_{i\in I}
c_i x_{ip}.
\]

Unidade: R$.

### \(f_2\): desvio quadrático de SiO2

\[
f_2(X)
=
\sum_{p\in P}
\left(
S_p - T_{g(p)}^{Si}
\right)^2.
\]

### \(f_3\): desvio quadrático de Al2O3

\[
f_3(X)
=
\sum_{p\in P}
\left(
A_p - T_{g(p)}^{Al}
\right)^2.
\]

O enunciado define a soma por pilha; portanto, nesta formulação inicial, cada pilha contribui uma vez para o objetivo, sem ponderação adicional por massa.

## 7. Representação computacional adotada

Cada pilha é representada por um vetor cujo comprimento é \(n_p\). Cada posição representa um caminhão e contém o identificador do minério correspondente.

Exemplo conceitual para uma pilha de 20 kt:

```text
[M3, M3, M5, M1, M7, M5, M4, M4, M6, M2]
```

Como a pilha tem 10 posições e cada posição representa 2 kt, a massa de 20 kt é preservada automaticamente.

A matriz de contagens \(x_{ip}\) é derivada dessa representação para avaliação eficiente.

## 8. Consequências da representação

- massa pode ser preservada por construção;
- integralidade de caminhões é automática;
- N1 pode ser uma substituição em uma posição;
- N2 pode ser uma troca entre duas posições;
- elegibilidade pode ser preservada filtrando os minérios permitidos antes do movimento;
- qualidade e disponibilidade ainda podem ser violadas e exigem política específica.

A política final de tratamento dessas inviabilidades está deliberadamente pendente.

## 9. Heurística construtiva baseline

A implementação inicial constrói uma solução que satisfaz por construção a massa das pilhas, a elegibilidade dos minérios e os limites mínimo e máximo globais de disponibilidade. Inicialmente são alocados os usos mínimos obrigatórios de cada minério. Em seguida, os slots restantes são preenchidos iterativamente com os minérios elegíveis de menor custo que ainda possuam disponibilidade.

Os limites de SiO₂ e Al₂O₃ não são considerados pela heurística construtiva baseline; portanto, a solução inicial pode ser inviável quanto à qualidade.

### 10. N3 — realocação com substituição em cadeia

A terceira vizinhança definida pelo grupo combina realocação e substituição. Para duas pilhas distintas, o minério de uma posição da primeira pilha é transferido para uma posição da segunda pilha, enquanto sua posição original recebe um novo minério elegível.

Esse movimento preserva massa e elegibilidade, mas pode alterar disponibilidade global, custo e qualidade. Diferentemente de N2, a composição global de minérios pode mudar.
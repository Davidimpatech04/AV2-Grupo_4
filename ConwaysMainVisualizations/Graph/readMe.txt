A ideia dessa visualização é transferir a idea do coway's game of life para um grafo
o grafo é construído com uma árvore minima geradora, que depois de conluida adiciona
mais arestas que o necessário para aumentar as interações

existem 3 facções nessa simulação, por nome e cor:

Legião Boros: Vermelhos
Casa Dimir: Azul
Enxame Golgari: Verdes

Também tem os bárbaros, que são cinzas e representam as célular mortas, existem 4 
possíveis intereções com suas chances de acontecerem

chance de um tile se tornar um bárbaro
chance de um bárbaro se unir a uma facção aleatória
chance de um tile se converter a uma facção se possuir devoção 1
chance de um tile se tornar um bárbaro se possuir devoção maior que 2

a devoção é a forma que eu usei para mensurar a quantiade de vizinhos de 
uma determinada facção.

para rpdar a simulação, execute o programa empire.py, ele possui uma lista com os
parâmetros citados para que possam ser alterados
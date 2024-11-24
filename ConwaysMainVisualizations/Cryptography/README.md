# AV2-Grupo_4 
## Criptografia básica usando Conway's Game of Life
A ideia está em gerar "mapas" para diferentes caracteres usando o Conway's Game of Life (CGoL). O processo de gerar um mapa para um caractere pode ser reduzido a:

• Obter um padrão inicial para o CGoL;

• Executar *n* passos;

• Extrair o mapa, traduzindo as linhas em strings (cada casa em uma linha vira 0 se estiver apagada e 1 caso contrário) e concatenando essas strings.

Após realizar esse processo para cada um dos caracteres que precisamos e obter a string que queremos encriptar, usamos um processo simples de cifra em cada caractere da string em seu respectivo mapa, se este existir, e obtemos finalmente uma string encriptada usando CGoL. As strings geradas usando este modelo são facilmente decriptadas se tivermos o mapa inicial.


O projeto tem severas limitações. Além de ser muito pouco eficiente para memória/tempo, por exemplo, os padrões usados para gerar o mapa de cada caractere devem ser cuidadosamente escolhidos, já que, dependendo do número de passos, podem morrer (todas as casas estão apagadas). Além disso, alguns padrões convergem num mesmo estilo final que outros, o que causaria colisões na hora de encriptar/decriptar uma mensagem.

O projeto pode ser expandido para tolerar uma quantidade infinita de caracteres teoricamente, porém, a necessidade por mais memória e padrões certificadamente funcionais aumenta rapidamente.

Um gerador aleatório de padrões pode até ser criado, porém, para este trabalho, criamos apenas uma versão básica do código, que tolera 7 caracteres com diferentes padrões.



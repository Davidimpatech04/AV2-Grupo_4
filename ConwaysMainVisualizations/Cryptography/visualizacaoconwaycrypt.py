import numpy as np

# Padrões predefinidos para alguns caracteres usando células do Jogo da Vida
PREDEFINED_PATTERNS = {
    "a": [(1, 1), (1, 2), (2, 1), (2, 2)],  # Bloco - Padrão fixo
    "b": [(1, 2), (2, 1), (2, 3), (3, 2)],  # Colmeia - Padrão fixo
    "c": [(1, 2), (2, 2), (3, 2)],          # Piscador - Padrão oscilador
    "d": [(1, 2), (1, 3), (1, 4), (2, 1), (2, 2), (2, 3)],  # Sapo - Padrão oscilador
    "e": [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)],  # Planador - Padrão gerador
    "f": [(0, 1), (0, 4), (1, 0), (1, 4), (2, 4), (3, 1), (3, 3)],  # LWSS - "Nave espacial leve" - Padrão gerador
}

# Função para dar um passo no Jogo da Vida de Conway. Segue as regras normais.
def conway_game_of_life_step(grid):
    rows, cols = grid.shape
    new_grid = np.zeros((rows, cols), dtype=int)  # Matriz para o novo estado
    for x in range(rows):
        for y in range(cols):
            neighbors = [(x-1, y-1), (x-1, y), (x-1, y+1), (x, y-1), (x, y+1), (x+1, y-1), (x+1, y), (x+1, y+1)]  #Coordenadas dos vizinhos no grid
            count = sum(grid[nx % rows, ny % cols] for nx, ny in neighbors)
            # Regras do Jogo da Vida
            if grid[x, y] == 1 and count in [2, 3]:  # Sobrevive
                new_grid[x, y] = 1
            elif grid[x, y] == 0 and count == 3:  # Nasce
                new_grid[x, y] = 1
    return new_grid

# Função para gerar o padrão final após um número de passos. Recebe os pontos iniciais, tamanho da grid (padrão 10x10) e o número de passos (padrão 10). Executa os passos e retorna uma string de 0 (azulejo apagado) e 1 (azulejo aceso)
def generate_game_pattern(starting_positions, grid_size=(10, 10), steps=10):

    grid = np.zeros(grid_size, dtype=int)  #Criando a grid vazia e definindo as posições iniciais baseadas no input da função
    for x, y in starting_positions:
        grid[x % grid_size[0], y % grid_size[1]] = 1
  
    for _ in range(steps): #Executando os passos
        grid = conway_game_of_life_step(grid)
    return ''.join(map(str, grid.flatten()))

# Função para criar o mapeamento de caracteres para padrões do Jogo da Vida. Para este trabalho, usamos apenas padrões predefinidos, porém o código pode ser extendido para gerar naturalmente padrões aleatórios para cada caractere.
def create_mapping(characters, steps=10, grid_size=(10, 10)):
    mapping = {}
    for char in characters: 
        if char in PREDEFINED_PATTERNS:
            starting_positions = PREDEFINED_PATTERNS[char]
      
        # Gera o padrão final após a evolução do Jogo da Vida
        final_state = generate_game_pattern(starting_positions, grid_size, steps)
        mapping[char] = final_state
    return mapping

# Função para criptografar a mensagem usando o mapeamento
def encrypt_message(message, mapping):
    return ''.join(mapping[char] for char in message if char in mapping)

# Função para descriptografar a mensagem usando o mapeamento invertido
def decrypt_message(encrypted_message, mapping):
    reverse_mapping = {v: k for k, v in mapping.items()}  # Gera o mapeamento inverso
    chunk_size = len(next(iter(mapping.values())))  # Obtém o tamanho de cada padrão

    #Quebra a mensagem em pedaços do tamanho de cada padrão, e usa o mapeamento inverso para obter a mensagem real
    return ''.join(reverse_mapping[encrypted_message[i:i+chunk_size]] 
                   for i in range(0, len(encrypted_message), chunk_size))

# Exemplo de uso simples

if __name__ == "__main__":
    characters = list("abcdef")  # Lista de caracteres a serem criptografados
    steps = 10  # Número de passos para evoluir o Jogo da Vida (padrão)
    grid_size = (10, 10)  # Tamanho da grade (padrão)

    # Gera o mapeamento de caracteres para padrões do Jogo da Vida
    mapping = create_mapping(characters, steps, grid_size)
    
    # Criptografa uma mensagem
    message = "abcdef"
    encrypted_message = encrypt_message(message, mapping)
    print("Mensagem Criptografada:", encrypted_message)

    # Descriptografa a mensagem
    decrypted_message = decrypt_message(encrypted_message, mapping)
    print("Mensagem Descriptografada:", decrypted_message)

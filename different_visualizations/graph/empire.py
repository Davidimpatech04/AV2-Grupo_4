import pygame
from modelo import Conway_empires
import numpy as np
import random
import math

def empire(
    cell,
    gradeX,
    gradeY,
    nodes,
    param,
    colors={"empty": (0, 0, 0), "filled": (255, 255, 255)},
    
):
    pygame.init()
    screen = pygame.display.set_mode((gradeX * cell, gradeY * cell ))
    clock = pygame.time.Clock()
    
    BLACK = (0, 0, 0)
    Barbarians = (255, 255, 255) 
    Fac = [
    (55, 182, 118),    # Golgari
    (246, 145, 168),   # Boros
    (73, 81, 131),     # Dimir
    ]
    
    
    def generate_grid(gradeX2, gradeY, num_vilas):
        grid = [[BLACK for _ in range(gradeX)] for _ in range(gradeY)]  # Grade inicial preta
        vilas = []

        for _ in range(num_vilas):
            x = random.randint(0, gradeX//2 - 1)
            y = random.randint(0, gradeY//2 - 1)
            grid[2*y][2*x] = random.choice(Fac)  # Escolhe uma facção aleatória
            vilas.append((2*x,2*y))
            
        for _ in range(num_vilas):
            x = random.randint(0, gradeX//2 - 1)
            y = random.randint(0, gradeY//2 - 1)
            grid[2*y][2*x] = Barbarians  
            vilas.append((2*x,2*y))
            
        return grid, vilas
    
    def draw_fac(grid, tile_size):
        for y, row in enumerate(grid):
            for x, color in enumerate(row):
                pygame.draw.rect(
                    screen,
                    color,
                    (x * tile_size, y * tile_size, tile_size, tile_size)
                )
                            
    def calculate_edges(vilas):
        edges = []
        for i, (x1, y1) in enumerate(vilas):
            for j, (x2, y2) in enumerate(vilas):
                if i < j:  # Evitar duplicação
                    weight = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                    edges.append((weight, (x1, y1), (x2, y2)))
        return edges
       
    def Amina(plano: list):

        n = len(plano)
        
        dist = [[0.0, 0]]*(n**2)
        
        for i in range(n):
            for j in range(n):
                dist[i*n + j] = [(plano[i][0] - plano[j][0])**2 + (plano[i][1] - plano[j][1])**2, i*n+j]
                
        dist.sort()
                
        link = [0]*n
        size = [0]*n
        
        for i in range(n):
            link[i] = i
            size[i] = 1
            
        def find(k):
            
            nonlocal link
            
            while k != link[k]:
                ram = link[k]
                k = ram
            
            return k
        
        def same(x, y):
            
            nonlocal find
            
            return find(x) == find(y)
        
        def unite(x, y):
            
            nonlocal find
            nonlocal size
            nonlocal link
            
            a = find(x)
            b = find(y)
            
            if ( size[a] < size[b]):
                a, b = b, a
                
            size[a] += size[b]
            link[b] = a   
    
        tree = []

        q = 0

        for d in dist:
            
            a = d[1]//n
            b = d[1]%n
            
            if not same(a,b):
                unite(a,b)
                tree.append([plano[a],plano[b]])
                q+=1
                
        
        id = 0
        id += q
        
        while(q):
            
            d = dist[id]
            q -=1
            id += 1
            
            a = d[1]//n
            b = d[1]%n
            
            tree.append([plano[a],plano[b]])
            

        return tree
                            
    def draw_connections(mst, tile_size):
            for (x1, y1), (x2, y2) in mst:
                pygame.draw.line(
                    screen,
                    (200, 200, 200),  # Cor da linha (cinza claro)
                    (x1 * tile_size + tile_size // 2, y1 * tile_size + tile_size // 2),
                    (x2 * tile_size + tile_size // 2, y2 * tile_size + tile_size // 2),
                    1  # Espessura da linha
                )
                
    grid, vilas = generate_grid(gradeX, gradeY, nodes)
    mst = Amina(vilas)
    
    model = Conway_empires(
        cell, gradeX, gradeY, nodes, vilas, mst, grid, param
    )
    
    running = True
    
    empty_color = colors["empty"]
    filled_color = colors["filled"]
    

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Atualiza a tela
        screen.fill(BLACK)
        draw_fac(grid, cell)
        draw_connections(mst, cell)
        pygame.display.flip()
        clock.tick(1)
        model.step()

    pygame.quit()
    
    
param = [
    50, # chance de um tile se tornar um bárbaro
    30, # chance de um bárbaro se unir a uma facção
    50, # chance de um tile se converter a uma facção se possuir devoção 1
    30, # chance de um tile se tornar um bárbaro se possuir devoção maior que 2
    
]
                
# os parâmetros são, tamanho do tile, largura da tela, altura da tela, e metade de quantidade total de tiles
empire(8,180, 80, 200, param)

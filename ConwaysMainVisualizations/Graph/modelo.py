import time
import random
import numpy as np
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import PropertyLayer

class Vertex:
    
    def __init__(self, val):
        self.val = val
        self.fac = ''
        self.adj = []
        self.devoc = [0,0,0]
        self.caos = 0
        self.next = ''


class G:    
    def __init__(self):
        self.Core = []
        
    def adjacent(self, x: Vertex, y: Vertex):
        if y in x.adj:
            return True
        return False

    def neighbors(self, x: Vertex):
        ans = []
        for v in x.adj:
            ans.append(v)
        return ans

    def add_vertex(self, x: Vertex):
        ans = True
        if x in self.Core:
            ans = False
        self.Core.append(x)
        return ans

    def remove_vertex(self, x: Vertex):     
        if x in self.Core:
            self.Core.remove(x)
            return True
        return False
    
    def add_edge(self, x: Vertex, y: Vertex):
        if (not y in x.adj ):
            x.adj.append(y)
            y.adj.append(x)
            return True
        return False
    
    def remove_edge(self, x: Vertex, y: Vertex):
        if (y in x.adj ):
            x.adj.remove(y)
            return True
        return False
        
    def get_vertex_value(self, x: Vertex):   
        return x.val

    def set_vertex_value(self, x: Vertex, v):     
        x.val = v

class Conway_empires(Model):
    
    
    
    def __init__(
        self,
        cell,
        gradeX,
        gradeY,
        nodes,
        vilas,
        mst,
        grid,
        param,
        
        
    ):
        self.graph = G()
        self.grid = grid
        self.chaos_rate = param[0]
        self.convoke_rate = param[1]
        self.dom_rate = param[2]
        self.break_rate = param[3]
        
        BLACK = (0, 0, 0)
        Barbarians = (255, 255, 255) 
        Fac = [
        (55, 182, 118),    # Golgari
        (246, 145, 168),   # Boros
        (73, 81, 131),     # Dimir
        ]
        
        super().__init__()
        self.cell_layer = PropertyLayer("cells", gradeX, gradeY, False, dtype=int)
           
        for v in vilas:
            x, y = v
            k = Vertex(v)
            if grid[y][x] == (55, 182, 118):
                    k.fac = 'Golgari'
            if grid[y][x] == (246, 145, 168):
                    k.fac = 'Boros'
            if grid[y][x] == (73, 81, 131):
                    k.fac = 'Dimir'
            if grid[y][x] == (255, 255, 255):
                    k.fac = 'Barbarian'
            
            self.graph.add_vertex(k)
            
        for m in mst:
            n1, n2 = m
            for v in self.graph.Core:
                if v.val == n1:
                    a = v
                if v.val == n2:
                    b = v
            self.graph.add_edge(a, b)
            
        
    def step(self):       
        
            for v in self.graph.Core:
                v.devoc = [0, 0, 0] # mede a devoção, AKA quantidade de vizinho de tal facção
                v.caos = 0 # mede o tanto de bárbaro perto
                N = self.graph.neighbors(v)
            

                for n in N: # calcula a devoção as facções baseado nos vizinhos
                    if n.fac == 'Golgari':
                        v.devoc[0] += 1
                    if n.fac == 'Boros':
                        v.devoc[1] += 1
                    if n.fac == 'Dimir':
                        v.devoc[2] += 1
                    if n.fac == 'Barbarian':
                        v.caos += 1

                p = random.randint(0,100)

                
                facs = ['Golgari', 'Boros', 'Dimir']
                dice = [0,1,2]
                
                random.shuffle(dice)
                
                changed = False
                
                if v.fac == 'Barbarian':
                    if p <= self.convoke_rate:
                        v.next = random.choice(facs)
                        changed = True
                        
                else:
                    if p <= self.chaos_rate:
                        changed = True
                        v.next = 'Barbarian'
                    
                    for i in dice:
                        if changed:
                            continue
                        if v.devoc[i] == 1 and p <= self.dom_rate:
                            v.next = facs[i]
                            changed = True
                        if v.devoc[i] >= 2 and p <= self.break_rate:
                            v.next = 'Barbarian'
                            changed = True
                            
                if not changed:
                    v.next = v.fac
                    

            # Atualiza as facções de cada vértice
            for v in self.graph.Core:
                v.fac = v.next
                x, y = v.val
                # Agora a cor depende da facção
                if v.fac == 'Golgari':
                    self.grid[y][x] = (55, 182, 118)
                elif v.fac == 'Boros':
                    self.grid[y][x] = (246, 145, 168)
                elif v.fac == 'Dimir':
                    self.grid[y][x] = (73, 81, 131)
                elif v.fac == 'Barbarian':
                    self.grid[y][x] = (255, 255, 255) 
            
            
            
                
            
                    
                
                        
                
                    
            

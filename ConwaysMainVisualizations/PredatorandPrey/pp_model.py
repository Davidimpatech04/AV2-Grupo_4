import numpy as np
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import PropertyLayer
from scipy.signal import convolve2d

from scipy.stats import expon
class GameOfLifeModel(Model):
    def __init__(
        self,
        lamb,
        width=10,
        height=10,
        alive_fraction=0.2,
#       game_type=[[2,3], [3]],
        game_type=[[0], [2]],
        probabilidade_presa=0.05,
        probabilidade_predador=0.1,

    ):
        super().__init__()
        # Initialize the property layer for cell states
        # [0->Vazio, 1->Presa, 2->Predador]
        self.cell_layer = PropertyLayer("cells", width, height, 0, dtype=int)

        self.time_no_eat = PropertyLayer("time", width, height, 0, dtype=int )
        # Parametro lambda da distribuição exponencial
        self.lamb = lamb
        # Randomly set cells to alive
        # Vamos determinar o número de presas e predador
        presa_inicializacao = np.random.choice(
            [0, 1],
            size=(width, height),
            p=[1 - probabilidade_presa, probabilidade_presa],
        )
        predador_inicializa = np.random.choice(
            [0, 2],
            size=(width, height),
            p=[1 - probabilidade_predador, probabilidade_predador],
        )
        self.cell_layer.data = np.maximum(presa_inicializacao, predador_inicializa)
        # Metrics and datacollector
        self.cells = width * height
        self.presas_count = 0
        self.preadores_count = 0
        self.datacollector = DataCollector(
            model_reporters={
                "Presas count": "self.presas_count",
                "Predador count": "self.preadores_count",
            }
        )
        self.datacollector.collect(self)
        self.game_type = game_type  # Matriz que determina a regra do jogo
    def step(self):
        # Define a kernel for counting neighbors. The kernel has 1s around the center cell (which is 0).
        kernel = np.array(
            [[1, 1, 1], [1, 0, 1], [1, 1, 1]]
        )  # Define a vizinhança, no nosso caso a vizinhança será Norte, Sul, Leste, Oeste
        # Count neighbors using convolution.
        neighbor_count = convolve2d(
            self.cell_layer.data, kernel, mode="same", boundary="wrap"
        )
        vizinhos_presas = convolve2d(
            self.cell_layer.data == 1, kernel, mode="same", boundary="wrap"
        )
        vizinhos_predadores = convolve2d(
            self.cell_layer.data == 2, kernel, mode="same", boundary="wrap"
        )
        # Cria uma cópia do estado atual para evitar alterações durante a iteração
        new_state = np.copy(self.cell_layer.data)
        # Regra para as presas:
        # 1. As presas sobrevivem se tiverem 2 ou 3 vizinhos do tipo "presa"
        # 2. As presas nascem se tiverem exatamente 3 vizinhos do tipo "presa"
        new_state = np.where(
            np.logical_or(
                np.logical_and(
                    self.cell_layer.data == 1,
                    np.isin(vizinhos_presas, self.game_type[0]),
                ),
                np.logical_and(
                    self.cell_layer.data == 0,
                    np.isin(vizinhos_presas, self.game_type[1]),
                ),
            ),
            1,
            0,
        )
        new_state[(self.cell_layer.data == 1) & (vizinhos_predadores > 0)] = (
            2  # Predadores sobrevivem e convertem presas em predadores
        )
        # Predadores morrem se não tiverem presas ao lado
        new_state[(self.cell_layer.data == 2) & (vizinhos_presas == 0)] = (
            0  # Predadores morrem se não houver presas
        )
        '''

        #Criação de um nomo modelo, as presas e os predadores se movem
        predador_positions = np.argwhere(self.cell_layer.data == 2) # Pegar todos os que são predadores
        presa_positions = np.argwhere(self.cell_layer.data == 1) # Pegar todos que são presas
        for pos in predador_positions:
            x, y = pos
            
            # O nosso modelo em um modelo sem bordas, podemos então não nos preucupar com o tamanho da matriz
            dx, dy = np.random.choice([-1, 0, 1], size=2)
            new_x, new_y = (x + dx) % self.cell_layer.width, (y + dy) % self.cell_layer.height
            
            if new_state[new_x, new_y] == 0:
                new_state[new_x, new_y] = 2
                self.time_no_eat.data[new_x, new_y] = self.time_no_eat.data[x,y]+1
                new_state[x, y] = 0
                self.time_no_eat.data[x,y] = 0
            # Uso de uma distribuição de probabilidade exponencial que almenta a probabilidade de uma célula morrer caso não coma
            morte_prob = expon.cdf(self.time_no_eat.data[new_x, new_y], scale= self.lamb)
            morta = np.random.rand() < morte_prob
            if morta:
                new_state[new_x, new_y] = 0
            
        for pos in presa_positions:#movimento da presa
            x, y = pos
            dx, dy = np.random.choice([-1, 0, 1], size=2)
            new_x, new_y = (x + dx) % self.cell_layer.width, (y + dy) % self.cell_layer.height

            if new_state[new_x, new_y] == 0:
                new_state[new_x, new_y] = 1
                new_state[x, y] = 0
        '''
        self.cell_layer.data = new_state
        # Atualiza o estado da camada de células
        self.cell_layer.data = new_state
        # Atualiza as métricas de presas e predadores
        self.presas_count = np.sum(self.cell_layer.data == 1)
        self.preadores_count = np.sum(self.cell_layer.data == 2)
        self.datacollector.collect(self)

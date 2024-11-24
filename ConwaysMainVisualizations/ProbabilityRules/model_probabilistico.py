import numpy as np
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import PropertyLayer
from scipy.signal import convolve2d
from scipy.stats import expon


class GameOfLifeModel(
    Model
):  # Aqui eu adicionei o revive_probabilities e o survive_probabilities
    def __init__(
        self,
        width=10,
        height=10,
        revive_probabilities=None,
        survive_probabilities=None,
        alive_fraction=0.2,
        lamb=1000,
        age_death=True,
    ):
        super().__init__()
        # Adicionei o parametro lambida da distibuição de probabilidade
        # Determina se a morte por idade está habilitado
        self.age_death = age_death
        # Initialize the property layer for cell states
        self.cell_layer = PropertyLayer("cells", width, height, False, dtype=bool)
        # Defino a idade de cada celula
        self.age_layer = PropertyLayer("ages", width, height, 0, dtype=int)
        self.cell_layer.data = np.random.choice(
            [True, False], size=(width, height), p=[alive_fraction, 1 - alive_fraction]
        )

        # Caso a probabilidade não seja dada, o padrão que o código vai seguir é o determinístico do jogo de Conway
        self.revive_probabilities = (
            revive_probabilities if revive_probabilities is not None else {3: 1.0}
        )
        self.survive_probabilities = (
            survive_probabilities
            if survive_probabilities is not None
            else {2: 1.0, 3: 1.0}
        )

        # Parametro lambida
        self.lamb = lamb

        # Metrics and datacollector
        self.cells = width * height
        self.alive_count = 0
        self.alive_fraction = 0
        self.datacollector = DataCollector(
            model_reporters={
                "Cells alive": "alive_count",
                "Fraction alive": "alive_fraction",
            }
        )
        self.datacollector.collect(self)

    def step(self):
        # Define a kernel for counting neighbors
        kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]])

        # Count neighbors
        neighbor_count = convolve2d(
            self.cell_layer.data, kernel, mode="same", boundary="wrap"
        )

        # Apply custom probabilistic rules for each cell
        new_state = np.zeros_like(self.cell_layer.data, dtype=bool)
        for x in range(self.cell_layer.data.shape[0]):
            for y in range(self.cell_layer.data.shape[1]):
                alive = self.cell_layer.data[x, y]
                neighbors = neighbor_count[x, y]
                idade = self.age_layer.data[x, y]
                if alive:
                    # Apply survival probability if the cell is alive
                    survival_prob = self.survive_probabilities.get(neighbors, 0)
                    # probabilidade de morte (quanto maior o lambida, menor vai ser com o tempo)
                    morte_prob = 0
                    if self.age_death:
                        morte_prob = expon.cdf(idade, scale=self.lamb)
                    # Retorna se conseguiu ou não sobreviver
                    viva = np.random.rand() < survival_prob
                    # Retorna se morreu ou não
                    morta = np.random.rand() < morte_prob
                    if viva and not morta:
                        new_state[x, y] = True
                    else:
                        new_state[x, y] = False
                    # Altera a idade
                    if not new_state[x, y]:
                        self.age_layer.data[x, y] = 0
                    else:
                        self.age_layer.data[x, y] += 1
                else:
                    # Apply revival probability if the cell is dead
                    revival_prob = self.revive_probabilities.get(neighbors, 0)
                    new_state[x, y] = np.random.rand() < revival_prob

        self.cell_layer.data = new_state

        # Update metrics
        self.alive_count = np.sum(self.cell_layer.data)
        self.alive_fraction = self.alive_count / self.cells
        self.datacollector.collect(self)

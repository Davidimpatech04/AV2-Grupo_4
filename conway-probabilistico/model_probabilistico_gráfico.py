# A ideia dessa modificação é implementar um gráfico de evolução da proporção células vivas/ total de células.

# The previous default libraries 
import numpy as np
import pygame
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import PropertyLayer
from scipy.signal import convolve2d
from scipy.stats import expon

# For the evolution graph ploting
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from multiprocessing import Process, Event, Manager
import time  # For adding a delay in the game initialization for the graphic to initialize before the game when graph = True.


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


# Para plotar o gráfico

def plot_graph(proportions, graph_event):
    # Configuração da figura do gráfico
    fig, ax = plt.subplots()
    fig.patch.set_facecolor('black')  # Fundo preto para a janela do gráfico
    ax.set_facecolor('black')  # Fundo preto para o gráfico

    x_data, y_data = [], []
    line, = ax.plot([], [], lw=2, color="cyan")  # Linha ciano para destaque no fundo preto

    def init_plot():
        ax.set_xlim(0, 100)  # Range inicial do eixo x
        ax.set_ylim(0, 1)  # Proporção de células vivas entre 0 e 1
        ax.set_title("Fraction of Alive Cells Over Time", color="white")  # Título branco
        ax.set_xlabel("Steps", color="white")  # Eixo x em branco
        ax.set_ylabel("Fraction Alive", color="white")  # Eixo y em branco
        ax.tick_params(axis='x', colors='white')  # Cor dos ticks do eixo x
        ax.tick_params(axis='y', colors='white')  # Cor dos ticks do eixo y
        return line,

    def update_plot(frame):
        if graph_event.is_set() and len(proportions) > 0:  # Atualiza somente quando não está pausado
            x_data.append(len(proportions))
            y_data.append(proportions[-1])
            line.set_data(x_data, y_data)

            # Ajustar dinamicamente o range do eixo y
            max_y = max(y_data)
            y_limit = min(1, 1.5 * max_y)
            ax.set_ylim(0, y_limit)

            ax.set_xlim(0, len(proportions) * 1.3)  # Ajustar dinamicamente o eixo x
        return line,

    ani = FuncAnimation(fig, update_plot, init_func=init_plot)
    plt.show()


def run_GameOfLifeModel(
    width,
    height,
    cell_size,
    revive_probabilities,
    survival_probabilities,
    lamb,
    age_death,
    initial_config=None,
    colors={"empty": (0, 0, 0), "filled": (255, 255, 255)},
    alive_fraction = 0.2,
    tick=20, 
    graph=False
):
    pygame.init()
    screen = pygame.display.set_mode((width * cell_size, height * cell_size + 100))  # Mais espaço para a barra de velocidade
    clock = pygame.time.Clock()

    model = GameOfLifeModel(
        width, height, revive_probabilities, survival_probabilities, alive_fraction, lamb, age_death
    )
    running = True
    paused = False
    dragging = False

    # Graph setup. Se graph == False, o código funciona exatamente como antes da modificação
    if graph:
        manager = Manager()
        proportions = manager.list()  # Para armazenar as proporções de cada passo (compartilhado entre processos)
        graph_event = Event()
        graph_event.set()  # Permitir atualizações inicialmente

        # Processo separado para o gráfico
        graph_process = Process(target=plot_graph, args=(proportions, graph_event))    # Separa o processo do gráfico para rodar em um processador diferente do game. (para evitar os bugs com fechar o game subitamente etc mencionados antes)
        graph_process.start()

        # Delay para permitir que a janela do gráfico abra antes de iniciar o game
        time.sleep(4)

    # Cores
    empty_color = colors["empty"]
    filled_color = colors["filled"]
    # Cores pros botões
    button_color = (200, 200, 200)
    button_hover_color = (150, 150, 150)

    clear_button_rect = pygame.Rect(10, height * cell_size + 10, 100, 30)

    # Barra deslizante para controle da velocidade
    slider_rect = pygame.Rect(10, height * cell_size + 50, 200, 20)  # Barra de controle
    slider_pos = 0  # Posição inicial do slider
    dragging_slider = False  # Variável para detectar o arraste do slider

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Eventos com o mouse
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if clear_button_rect.collidepoint(mouse_x, mouse_y):
                    model.cell_layer.data = np.zeros((width, height), dtype=bool)  
                elif slider_rect.collidepoint(mouse_x, mouse_y):  # Interação com a barra deslizante
                    slider_pos = max(0, min(200, mouse_x - slider_rect.x))  # Limita o valor do slider
                    dragging_slider = True
                else:
                    dragging = True
                    grid_x = mouse_x // cell_size
                    grid_y = mouse_y // cell_size
                    if 0 <= grid_x < width and 0 <= grid_y < height:
                        model.cell_layer.data[grid_x, grid_y] = not model.cell_layer.data[grid_x, grid_y]

            elif event.type == pygame.MOUSEBUTTONUP:
                dragging_slider = False
                dragging = False

            # Eventos com o teclado
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                    if paused:
                        graph_event.clear()  # Pausar atualizações do gráfico
                    else:
                        graph_event.set()  # Retomar atualizações do gráfico
                        
        # Lida com o dragging do mouse (movimentação contínua do slider)
        if dragging_slider:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            slider_pos = max(0, min(200, mouse_x - slider_rect.x))  # Limita a posição do slider

        # Atualiza a velocidade com base na posição do slider
        speed = 200 - slider_pos  # Quanto mais à direita, mais lento
        
        # Se a velocidade for 0, pausa o jogo
        if speed == 0:
            paused = True
            graph_event.clear()
            
        clock.tick(speed)

        screen.fill((0, 0, 0)) 

        # Renderizando as células com transição de cor suave
        for x in range(width):
            for y in range(height):
                if model.cell_layer.data[x][y]:  
                    age = model.age_layer.data[x][y]  

                    red_intensity = min(255, max(0, age * 5))  
                    green_intensity = max(0, 255 - age * 5) 
                    blue_intensity = max(0, 255 - age * 5)  

                    cell_color = (red_intensity, green_intensity, blue_intensity) 

                else:
                    cell_color = empty_color

                pygame.draw.rect(
                    screen,
                    cell_color,
                    (x * cell_size, y * cell_size, cell_size, cell_size)
                )

        # Interação com o botão de limpar
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if clear_button_rect.collidepoint(mouse_x, mouse_y):
            pygame.draw.rect(screen, button_hover_color, clear_button_rect)
        else:
            pygame.draw.rect(screen, button_color, clear_button_rect)

        font = pygame.font.SysFont(None, 24)
        text = font.render("Clear", True, (0, 0, 0))
        screen.blit(text, (clear_button_rect.x + 25, clear_button_rect.y + 5))

        # Exibe a barra deslizante
        pygame.draw.rect(screen, (255, 255, 255), slider_rect, 2)  # Caixa do slider
        pygame.draw.circle(screen, (255, 0, 0), (slider_rect.x + slider_pos, slider_rect.centery), 10)  # Controle do slider

        # Exibe a velocidade atual na tela
        speed_text = f"Speed: {200 - slider_pos}"
        speed_surface = pygame.font.SysFont(None, 24).render(speed_text, True, (255, 255, 255))
        screen.blit(speed_surface, (slider_rect.x + 220, slider_rect.y))

        # Mostrar o status de pausa
        pause_text = "PAUSED" if paused else "RUNNING"
        pause_color = (255, 0, 0) if paused else (0, 255, 0)
        pause_font = pygame.font.SysFont(None, 30)
        pause_surface = pause_font.render(pause_text, True, pause_color)
        screen.blit(pause_surface, (width * cell_size - 120, height * cell_size + 10))

        # Exibindo o número de células vivas e a fração
        alive_count_text = font.render(f"Vivas: {model.alive_count}", True, (255, 255, 255))
        screen.blit(alive_count_text, (10, 10))

        pygame.display.flip()

        if not paused:
            model.step()
            if graph:
                proportions.append(model.alive_fraction)
    
    if graph:
        graph_process.terminate()  # Fechar o processo do gráfico ao encerrar

    pygame.quit()

"""Um exemplo onde todas as regras permanecem, com a exceção de que as vezes uma célula revive sozinha
É curioso que nesse caso ela pode aparecer perto de uma estrutura estável, fazendo com que esta desestabilize e desapareça
ou (o que é um pouco menos provável) cresça caoticamente"""

if __name__ == '__main__':
    run_GameOfLifeModel(120, 70, 10, {0: 0.001, 3: 1.0}, {2: 1, 3: 1}, 10000, True, graph=True)

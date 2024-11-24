# Imports (including necessary for graphing and multiprocessing)
import numpy as np
import pygame
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import PropertyLayer
from scipy.signal import convolve2d
from scipy.stats import expon
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from multiprocessing import Process, Event, Manager
import time


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
            if len(proportions) < len(x_data):
                # Reset data on graph when graph data resets
                x_data.clear()
                y_data.clear()

            x_data.append(len(proportions))
            y_data.append(proportions[-1])
            line.set_data(x_data, y_data)

            # Ajustar dinamicamente o range do eixo y
            max_y = max(y_data)
            y_limit = min(1, 1.3 * max_y)
            ax.set_ylim(0, y_limit)

            ax.set_xlim(0, len(proportions) * 1.3)  # Ajustar dinamicamente o eixo x
        return line,

    ani = FuncAnimation(fig, update_plot, init_func=init_plot)
    plt.show()


def run_GameOfLifeModel(
    cell_size,
    revive_probabilities,
    survival_probabilities,
    lamb,
    age_death,
    initial_config=None,
    colors={"empty": (0, 0, 0), "filled": (255, 255, 255)},
    alive_fraction = 0.2,
    tick=20,
    graph=False,
    screen_size=None
):
    """
    Função principal para executar o jogo da vida probabilístico.

    Args:
        width (int): Largura da grade (número de células).
        height (int): Altura da grade (número de células).
        cell_size (int): Tamanho de cada célula em pixels.
        revive_probabilities (dict): Probabilidades de reviver células.
        survival_probabilities (dict): Probabilidades de sobrevivência.
        lamb (float): Constante lambda para ajuste.
        age_death (bool): Define se idade influencia na morte.
        initial_config (np.array, optional): Configuração inicial das células.
        colors (dict): Cores para células vivas e mortas.
        alive_fraction (float): Fração inicial de células vivas.
        tick (int): Velocidade inicial da simulação.
        graph (bool): Define se o gráfico (step, alive_fraction) será plotado
        screen_size: tamanho de inicialização da tela
    """

    # Definição de cores para células e botões
    empty_color = colors["empty"]
    filled_color = colors["filled"]
    button_color = (200, 200, 200)
    button_hover_color = (150, 150, 150)

        # Inicializa as configurações do gráfico se graph == True
    if graph:
        manager = Manager()
        proportions = manager.list()
        graph_event = Event()
        graph_event.set()  # Inicia os updates no gráfico

        # Inicia o gráfico como um processo separado
        graph_process = Process(target=plot_graph, args=(proportions, graph_event))
        graph_process.start()

        # Delay para que o jogo inicie depois que o gráfico estiver configurado
        time.sleep(4)

    def initialize_pygame(cell_size, screen_size):
        """
        Inicializa o Pygame em modo janela com tamanho flexível.
        """
        pygame.init()
        
        if not screen_size: # plota em tela cheia
            display_info = pygame.display.Info()
            screen_width = display_info.current_w  # Largura da tela em pixels
            screen_height = display_info.current_h  # Altura da tela em pixels
        else:
            screen_width, screen_height = screen_size
            screen = pygame.display.set_mode(screen_size)  # modo janela
        
        # Ajusta a largura e comprimento
        width = (screen_width) // cell_size
        height = (screen_height - 100) // cell_size  # Subtraímos 100 pixels para os controles

        screen = pygame.display.set_mode((screen_width, screen_height))
        
        clock = pygame.time.Clock()

        return screen, clock, width, height
    
    def setup_buttons(screen_width, screen_height):
        """
        Ajusta o tamanho dos botões dinamicamente para qualquer tamanho razoável de janela.
        """
        button_area_y = screen_height - 90  # Coloca os botões a 90 pixels da parte de baixo da janela
        button_width = min(100, screen_width // 6)  # Ajusta dinamicamente o tamanho dos botões com um limite de 100 pixels
        button_spacing = 10  # Espaço entre os botões

        # Calcula as coordenadas x dos botões
        clear_button_rect = pygame.Rect(10, button_area_y, button_width, 30)
        random_button_rect = pygame.Rect(clear_button_rect.right + button_spacing, button_area_y, button_width, 30)
        exit_button_rect = pygame.Rect(random_button_rect.right + button_spacing, button_area_y, button_width, 30)

        return clear_button_rect, random_button_rect, exit_button_rect
    
    def setup_sliders(screen_width, screen_height):
        """
        Ajusta o tamanho dos sliders dinamicamente para qualquer tamanho razoável de janela.
        """
        slider_area_y = screen_height - 30  # Coloca os sliders a 30 pixels da parte de baixo da janela

        # Calcula a largura de cada slider como uma fração da largura da janela, com um mínimo e um máximo
        slider_width = max(150, min(200, screen_width // 5.5))
        slider_height = 20
        slider_spacing = 55  # Espaço entre os sliders

        # Calcula as coordenadas x de cada slider baseadas na largura e espaçamento
        slider_speed_x = 10
        slider_respawn_x = slider_speed_x + slider_width + slider_spacing
        slider_density_x = slider_respawn_x + slider_width + slider_spacing
        slider_cell_size_x = slider_density_x + slider_width + slider_spacing

        slider_speed = pygame.Rect(slider_speed_x, slider_area_y, slider_width, slider_height)
        slider_respawn = pygame.Rect(slider_respawn_x, slider_area_y, slider_width, slider_height)
        slider_density = pygame.Rect(slider_density_x, slider_area_y, slider_width, slider_height)
        slider_cell_size = pygame.Rect(slider_cell_size_x, slider_area_y, slider_width, slider_height)

        sliders = {
            "slider1": {"rect": slider_speed, "pos": 20, "label": "Speed"},
            "slider2": {"rect": slider_respawn, "pos": 100, "label": "Respawn %"},
            "slider3": {"rect": slider_density, "pos": 100, "label": "Init Density"},
            "slider4": {"rect": slider_cell_size, "pos": 50, "label": "Cell Size"}
        }
        return sliders

    def handle_events(
        model, width, height, cell_size, clear_button_rect, random_button_rect, exit_button_rect,
        sliders, paused, dragging_slider
    ):
        """
        Processa eventos do usuário, incluindo mouse, teclado e interação com botões.
        """
        running = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()

                # Botões
                if clear_button_rect.collidepoint(mouse_x, mouse_y):
                    model.cell_layer.data = np.zeros((width, height), dtype=bool)
                    if graph and proportions is not None:
                        proportions[:] = []    # Reinicia o gráfico com o clique

                elif random_button_rect.collidepoint(mouse_x, mouse_y):
                    slider3 = sliders['slider3']
                    alive_fraction = slider3['pos']/200
                    model.cell_layer.data = np.random.rand(width, height) <= alive_fraction
                    if graph and proportions is not None:
                        proportions[:] = []  # Reinicia o gráfico com o clique

                elif exit_button_rect.collidepoint(mouse_x, mouse_y):  
                    running = False

                for key, slider in sliders.items():
                    if slider["rect"].collidepoint(mouse_x, mouse_y):
                        dragging_slider[key] = True  # Começa a arrastar
                        slider["pos"] = max(0, min(200, mouse_x - slider["rect"].x))

                # Interação com células
                else:
                    grid_x = mouse_x // cell_size
                    grid_y = mouse_y // cell_size
                    if 0 <= grid_x < width and 0 <= grid_y < height:
                        click_buffer[grid_x, grid_y] = not click_buffer[grid_x, grid_y]

            elif event.type == pygame.MOUSEBUTTONUP:
                for key in dragging_slider:
                    dragging_slider[key] = False

            elif event.type == pygame.MOUSEMOTION:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                for key, slider in sliders.items():
                    if dragging_slider.get(key, False):
                        slider["pos"] = max(0, min(200, mouse_x - slider["rect"].x))

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused

        # Calcula valores normalizados dos sliders
        slider_values = {key: slider["pos"] / 200 for key, slider in sliders.items()}
        return running, paused, dragging_slider, slider_values
        
    def draw_cells(screen, model, cell_size, width, height, empty_color):
        """
        Renderiza as células com base no estado do modelo.
        """
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

    def draw_button(screen, rect, text, font, mouse_pos, color, hover_color):
        """
        Renderiza um botão na tela.
        """
        if rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, hover_color, rect)
        else:
            pygame.draw.rect(screen, color, rect)

        button_text = font.render(text, True, (0, 0, 0))
        screen.blit(button_text, (rect.x + 15, rect.y + 5))

    def render_game(screen, model, cell_size, width, height, empty_color):
        """
        Renderiza o estado atual do jogo na tela.
        """
        screen.fill((0, 0, 0))  # Limpa a tela
        draw_cells(screen, model, cell_size, width, height, empty_color)

    def render_buttons(screen, font, mouse_pos, clear_button_rect, random_button_rect, exit_button_rect, button_color, button_hover_color):
        """
        Renderiza os botões na tela.
        """
        draw_button(screen, clear_button_rect, "Clear", font, mouse_pos, button_color, button_hover_color)
        draw_button(screen, random_button_rect, "Random", font, mouse_pos, button_color, button_hover_color) 
        draw_button(screen, exit_button_rect, "Exit", font, mouse_pos, button_color, button_hover_color) 

    def render_sliders(screen, font, sliders):
        """
        Renderiza os sliders na tela.
        """
        for key, slider in sliders.items():
            # Desenha a legenda em cima do slider
            label = font.render(slider["label"], True, (255, 255, 255))
            screen.blit(label, (slider["rect"].x, slider["rect"].y - 20))  # Coloca a legenda 20 pixels acima do slider

            # Desenha o slider
            pygame.draw.rect(screen, (255, 255, 255), slider["rect"], 2)  # Slider outline
            pygame.draw.circle(screen, (255, 0, 0), (slider["rect"].x + slider["pos"], slider["rect"].centery), 10)

        # Valor do slider (de 0 a 50) para a velocidade
        slider1 = sliders['slider1']
        value = int(slider1["pos"] / 200 * 50)  # Escala o valor de 0 a 50
        value_text = font.render(f"{value:.1f}", True, (255, 255, 255))
        screen.blit(value_text, (slider1["rect"].x + slider1["rect"].width + 10, slider1["rect"].y))
        # Valor do slider (de 0% a 2%) para o respawn
        slider2 = sliders['slider2']
        value = slider2["pos"] / 10000  # Escala o valor de 0 a 0.02
        value_text = font.render(f"{100*value:.2f}", True, (255, 255, 255))
        screen.blit(value_text, (slider2["rect"].x + slider2["rect"].width + 10, slider2["rect"].y))
        revive_probabilities[0] = value
        # Ajustar a densidade
        slider3 = sliders['slider3']
        value = slider3["pos"] / 200  # Densidade de 0 a 1
        value_text = font.render(f"{value:.2f}", True, (255, 255, 255))
        screen.blit(value_text, (slider3["rect"].x + slider3["rect"].width + 10, slider3["rect"].y))
        # Valor do slider (de 5 a 50 pixels) para o tamanho das células
        slider4 = sliders['slider4']
        value = int(slider4["pos"] / 200 * 45 + 5)  # Escala o valor de 5 a 50
        value_text = font.render(f"{value}", True, (255, 255, 255))
        screen.blit(value_text, (slider4["rect"].x + slider4["rect"].width + 10, slider4["rect"].y))

    def render_status(screen, font, width, cell_size, paused):
        """
        Exibe o status de pausa/execução do jogo.
        """
        pause_text = "PAUSED" if paused else "RUNNING"
        pause_color = (255, 0, 0) if paused else (0, 255, 0)
        pause_surface = pygame.font.SysFont(None, 30).render(pause_text, True, pause_color)

        display_info = pygame.display.Info()
        screen_width = display_info.current_w  # Largura da tela em pixels
        screen_height = display_info.current_h  # Altura da tela em pixels
        screen.blit(pause_surface, (screen_width - 120, screen_height - 80))

    def render_model_info(screen, font, model, max_age):
        """
        Exibe informações do modelo: células vivas, idade média e máxima.
        """
        try:
            average_age = np.mean(model.age_layer.data[model.cell_layer.data])
            max_age = max(max_age, np.max(model.age_layer.data[model.cell_layer.data]))
        except:
            average_age = 0

        alive_count_text = font.render(f"Vivas: {model.alive_count}", True, (255, 255, 255))
        avg_age_text = font.render(f"Idade Média: {average_age:.2f}", True, (255, 255, 255))
        max_age_text = font.render(f"Idade Máxima: {max_age}", True, (255, 255, 255))
        
        screen.blit(alive_count_text, (10, 10))
        screen.blit(avg_age_text, (10, 30))
        screen.blit(max_age_text, (10, 50))

        return max_age  # Atualiza o valor de idade máxima
    
    # Inicialização do jogo
    if not screen_size and graph: # valor default para graph == True e tamanho da tela não dado
        screen_size = (1130, 680)
    # Slider está com problema de renderização para largura screen_size menor que (1100, y). Na prática, o jogo funciona igual, é só um problema de vizualização
    screen, clock, width, height = initialize_pygame(cell_size, screen_size)
    model = GameOfLifeModel( # Instancia o modelo do jogo.
        width, height, revive_probabilities, survival_probabilities, alive_fraction, lamb, age_death
    ) 
    clear_button_rect, random_button_rect, exit_button_rect = setup_buttons(screen.get_width(), screen.get_height()) # Configuração dos botões.
    sliders = setup_sliders(screen.get_width(), screen.get_height()) # Configuração inicial dos sliders
    font = pygame.font.SysFont(None, 24) # Fonte usada nos textos.
    running, paused = True, False # Estados iniciais do jogo.
    dragging_slider = {key: False for key in sliders}  # Inicialização do estado de arraste
    max_age = 0 # Idade máxima inicial.
    click_buffer = np.zeros((width, height), dtype=bool)

    # Loop Principal do jogo.
    while running:
        mouse_pos = pygame.mouse.get_pos()
        running, paused, dragging_slider, slider_values = handle_events(
            model, width, height, cell_size, clear_button_rect, random_button_rect, exit_button_rect,
            sliders, paused, dragging_slider
        )
        speed = int(slider_values["slider1"] * 50)

        if speed != 0:
            clock.tick(speed)  # Ajusta a velocidade do jogo

        if speed == 0:
            paused = True

        if not paused:
            model.step()
        model.cell_layer.data = np.logical_or(model.cell_layer.data, click_buffer)
        click_buffer.fill(False)

        if not paused:
            if graph:
                proportions.append(model.alive_fraction)

        new_cell_size = int(slider_values["slider4"] * 45 + 5)

        # Se o tamanho das células mudou, recalcular a grade
        if new_cell_size != cell_size:
            cell_size = new_cell_size
            width = screen.get_width() // cell_size
            height = (screen.get_height() - 100) // cell_size
            model = GameOfLifeModel(
                width, height, revive_probabilities, survival_probabilities, alive_fraction, lamb, age_death
            )
            # Reinicialize o click_buffer para o novo tamanho
            click_buffer = np.zeros((width, height), dtype=bool)

        # Renderização
        screen.fill((0, 0, 0))
        render_game(screen, model, cell_size, width, height, empty_color)
        render_buttons(screen, font, mouse_pos, clear_button_rect, random_button_rect, exit_button_rect, button_color, button_hover_color)
        render_sliders(screen, font, sliders)
        render_status(screen, font, width, cell_size, paused)
        max_age = render_model_info(screen, font, model, max_age)
        pygame.display.flip()

    if graph:
        graph_process.terminate()

    pygame.quit()

if __name__ == '__main__':
    run_GameOfLifeModel(10, {0: 0.001, 3: 1.0}, {2: 1, 3: 1}, 1050, False, graph=True)
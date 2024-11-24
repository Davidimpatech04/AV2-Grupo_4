import pygame
from model_probabilistico import GameOfLifeModel # Modelo do jogo
import numpy as np
import math

def run_GameOfLifeModel(
    cell_size,
    revive_probabilities,
    survival_probabilities,
    lamb,
    age_death,
    initial_config=None,
    colors={"empty": (0, 0, 0), "filled": (255, 255, 255)},
    alive_fraction = 0.2,
    tick=20 
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
    """

    # Definição de cores para células e botões
    empty_color = colors["empty"]
    filled_color = colors["filled"]
    button_color = (200, 200, 200)
    button_hover_color = (150, 150, 150)

    def initialize_pygame(cell_size):
        """
        Inicializa o Pygame em modo tela cheia e configura o relógio.
        Calcula o número de células baseado na resolução da tela.
        """
        pygame.init()

        # Obtém informações da tela
        display_info = pygame.display.Info()
        screen_width = display_info.current_w  # Largura da tela em pixels
        screen_height = display_info.current_h  # Altura da tela em pixels

        # Ajusta a largura e comprimento
        width = (screen_width) // cell_size
        height = (screen_height - 100) // cell_size  # Subtraímos 100 pixels para os controles

        # Configura a tela em modo tela cheia
        screen = pygame.display.set_mode((screen_width, screen_height))
        clock = pygame.time.Clock()

        return screen, clock, width, height
    
    def setup_buttons(cell_size, height):
        """
        Configura os botões Clear, Random e Exit.
        """
        clear_button_rect = pygame.Rect(10, height * cell_size + 10, 100, 30)
        random_button_rect = pygame.Rect(120, height * cell_size + 10, 100, 30)
        exit_button_rect = pygame.Rect(230, height * cell_size + 10, 100, 30)  # Novo botão "Exit"
        return clear_button_rect, random_button_rect, exit_button_rect
    
    def setup_sliders(cell_size, height):
        """
        Configura dois sliders lado a lado.
        """
        slider_speed = pygame.Rect(10, height * cell_size + 70, 200, 20)
        slider_respawn = pygame.Rect(260, height * cell_size + 70, 200, 20)
        slider_density = pygame.Rect(520, height * cell_size + 70, 200, 20)
        slider_cell_size = pygame.Rect(780, height * cell_size + 70, 200, 20)

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
                elif random_button_rect.collidepoint(mouse_x, mouse_y):
                    slider3 = sliders['slider3']
                    alive_fraction = slider3['pos']/200
                    model.cell_layer.data = np.random.rand(width, height) <= alive_fraction
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
        Renderiza múltiplos sliders lado a lado.
        """
        for key, slider in sliders.items():
            # Caixa do slider
            pygame.draw.rect(screen, (255, 255, 255), slider["rect"], 2)

            # Controle do slider
            pygame.draw.circle(
                screen, (255, 0, 0), (slider["rect"].x + slider["pos"], slider["rect"].centery), 10
            )

            # Rótulo do slider
            label = font.render(slider["label"], True, (255, 255, 255))
            screen.blit(label, (slider["rect"].x, slider["rect"].y - 20))

        # Valor do slider (de 0 a 50) para a velocidade
        slider1 = sliders['slider1']
        value = int(slider1["pos"] / 200 * 50)  # Escala o valor de 0 a 50
        value_text = font.render(f"{value:.1f}", True, (255, 255, 255))
        screen.blit(value_text, (slider1["rect"].x + slider1["rect"].width + 10, slider1["rect"].y))
        # Valor do slider (de 0% a 0.02%) para o respawn
        slider2 = sliders['slider2']
        value = slider2["pos"] / 10000  # Escala o valor de 0 a 0.02
        value_text = font.render(f"{value:.3f}", True, (255, 255, 255))
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
    screen, clock, width, height = initialize_pygame(cell_size)
    model = GameOfLifeModel( # Instancia o modelo do jogo.
        width, height, revive_probabilities, survival_probabilities, alive_fraction, lamb, age_death
    ) 
    clear_button_rect, random_button_rect, exit_button_rect = setup_buttons(cell_size, height) # Configuração dos botões.
    sliders = setup_sliders(cell_size, height)  # Configuração inicial dos sliders
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

    pygame.quit()


run_GameOfLifeModel(10, {0: 0.001, 3: 1.0}, {2: 1, 3: 1}, 1050, False)
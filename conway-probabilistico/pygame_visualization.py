import pygame
from model_probabilistico import GameOfLifeModel
import numpy as np

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
    tick=20 
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

        # Lida com o dragging do mouse (movimentação contínua do slider)
        if dragging_slider:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            slider_pos = max(0, min(200, mouse_x - slider_rect.x))  # Limita a posição do slider

        # Atualiza a velocidade com base na posição do slider
        speed = 200 - slider_pos  # Quanto mais à direita, mais lento
        
        # Se a velocidade for 0, pausa o jogo
        if speed == 0:
            paused = True

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

    pygame.quit()

"""Um exemplo onde todas as regras permanecem, com a exceção de que as vezes uma célula revive sozinha
É curioso que nesse caso ela pode aparecer perto de uma estrutura estável, fazendo com que esta desestabilize e desapareça
ou (o que é um pouco menos provável) cresça caoticamente"""
run_GameOfLifeModel(120, 70, 10, {0: 0.001, 3: 1.0}, {2: 1, 3: 1}, 1000, False)
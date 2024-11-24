from pp_model import GameOfLifeModel
import pygame
import matplotlib.pyplot as plt


def run_GameOfLifeModel(
    width,
    height,
    cell_size,
    lamb,
    initial_config=None,
    colors={"empty": (0, 255, 0), "prey": (255, 255, 0), "predator": (255, 0, 0)},
):
    pygame.init()
    screen = pygame.display.set_mode((width * cell_size, height * cell_size + 100))  # Adicionando espaço para o controle de velocidade
    clock = pygame.time.Clock()

    # Corrigindo a criação do modelo para garantir que lamb seja utilizado corretamente
    model = GameOfLifeModel(lamb,width, height, alive_fraction=0.2)
    running = True
    paused = False  # Para controlar a pausa do jogo
    last_click_time = 0  # Para controlar o clique duplo

    # Alterando a cor de fundo para preto
    empty_color = (0, 0, 0)  # Cor preta para o fundo
    prey_color = colors["prey"]  # Cor para presas
    predator_color = colors["predator"]  # Cor para predadores

    # Definir a área do botão RESET (na parte inferior esquerda)
    reset_button_rect = pygame.Rect(10, height * cell_size - 40, 100, 30)

    # Listas para armazenar os dados de presas e predadores

    prey_counts = []
    predator_counts = []
    time_steps = []
    time_step = 0

    # Barra de controle de velocidade
    slider_rect = pygame.Rect(10, height * cell_size + 50, 200, 20)  # Caixa do slider
    slider_pos = 100  # Posição inicial do slider (100 => 50% da velocidade)
    dragging_slider = False

    # Velocidade inicial de simulação
    base_speed = 10  # Base da velocidade (quanto maior, mais rápido)
    max_speed = 100  # Velocidade máxima

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Pausar/despausar
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused

            # Detecção de cliques
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                grid_x, grid_y = mouse_x // cell_size, mouse_y // cell_size

                # Clique no botão RESET
                if reset_button_rect.collidepoint(mouse_x, mouse_y):
                    model = GameOfLifeModel(lamb,width, height, alive_fraction=0.2)  # Reiniciar o modelo
                elif slider_rect.collidepoint(mouse_x, mouse_y):
                    slider_pos = max(0, min(200, mouse_x - slider_rect.x))
                    dragging_slider = True
                else:
                    # Clique simples ou duplo
                    current_time = pygame.time.get_ticks()
                    if current_time - last_click_time < 500:
                        model.cell_layer.data[grid_x][grid_y] = 1  # Presa
                    else:
                        model.cell_layer.data[grid_x][grid_y] = 2  # Predador
                    last_click_time = current_time

            if event.type == pygame.MOUSEBUTTONUP:
                dragging_slider = False

            # Mover o slider quando ele está sendo arrastado
            if dragging_slider and event.type == pygame.MOUSEMOTION:
                mouse_x, _ = event.pos
                slider_pos = max(0, min(200, mouse_x - slider_rect.x))

        # Atualizar a velocidade com base no slider
        speed_factor = slider_pos / 200  # Ajusta a velocidade com base na posição do slider (0 a 1)
        speed = base_speed * (speed_factor + 0.3)


        if not paused:
            model.step()

        prey_count = sum(1 for x in range(width) for y in range(height) if model.cell_layer.data[x][y] == 1)
        predator_count = sum(1 for x in range(width) for y in range(height) if model.cell_layer.data[x][y] == 2)
        # Armazenar os dados
        prey_counts.append(prey_count)
        predator_counts.append(predator_count)
        time_steps.append(time_step)
        time_step += 1


        screen.fill(empty_color)  # Limpar tela com fundo preto


        # Desenho das células
        for x in range(width):
            for y in range(height):
                if model.cell_layer.data[x][y] == 1:
                    pygame.draw.rect(screen, prey_color, (x * cell_size, y * cell_size, cell_size, cell_size))
                elif model.cell_layer.data[x][y] == 2:
                    pygame.draw.rect(screen, predator_color, (x * cell_size, y * cell_size, cell_size, cell_size))

        # Desenhando a barra deslizante (sl10)ider)
        pygame.draw.rect(screen, (255, 255, 255), slider_rect, 2)  # Caixa do slider
        pygame.draw.circle(screen, (255, 0, 0), (slider_rect.x + slider_pos, slider_rect.centery), 10)

        # Desenhando o botão RESET
        pygame.draw.rect(screen, (200, 200, 200), reset_button_rect)
        font = pygame.font.SysFont("Arial", 20)
        text = font.render("RESET", True, (0, 0, 0))
        screen.blit(text, (reset_button_rect.x + 20, reset_button_rect.y + 5))

        # Exibindo o contador de presas e predadores
        counter_font = pygame.font.SysFont("Arial", 24)
        prey_text = counter_font.render(f"Presas: {prey_count}", True, (0, 255, 0))  # Cor verde para presas
        predator_text = counter_font.render(f"Predadores: {predator_count}", True, (255, 0, 0))  # Cor vermelha para predadores
        screen.blit(prey_text, (900, 710))  # Exibindo o contador de presas 
        screen.blit(predator_text, (900, 740))  # Exibindo o contador de predadores logo abaixo
        
        # Adicionando a palavra 'Velocidade' acima do slider
        rate_font = pygame.font.SysFont("Arial", 20)
        rate_text = rate_font.render("Velocidade:", True, (255, 255, 255))  # Cor branca para o texto
        screen.blit(rate_text, (slider_rect.x + (slider_rect.width // 2) - rate_text.get_width() // 2, slider_rect.y - 30))

        # Mostrar o status de pausa
        pause_text = "PAUSED" if paused else "RUNNING"
        pause_color = (255, 0, 0) if paused else (0, 255, 0)
        pause_font = pygame.font.SysFont(None, 30)
        pause_surface = pause_font.render(pause_text, True, pause_color)
        screen.blit(pause_surface, (width * cell_size - 120, height * cell_size + 10))

        pygame.display.flip()  # Atualizar a tela
        clock.tick(speed)  # Ajusta a velocidade com base no slider (quanto maior o valor de speed, mais rápido será)

    pygame.quit()  # Finaliza o pygame


    # Plotando o gráfico
    plt.figure(figsize=(10, 6))
    plt.plot(time_steps, prey_counts, label="Presas", color="green")
    plt.plot(time_steps, predator_counts, label="Predadores", color="red")
    plt.xlabel("Tempo (Passos)")
    plt.ylabel("Quantidade")
    plt.title("Dinâmica Predador-Prey ao Longo do Tempo")
    plt.legend()
    plt.grid(True)
    plt.show()

# Chamar a função para rodar o modelo
run_GameOfLifeModel(120, 70, 10,10)

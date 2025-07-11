import pygame as pg
import sys
import pyautogui
import pickle
import os

# Инициализация pygame
pg.init()
screen = pg.display.set_mode((960, 960))
pg.display.set_caption("Игра Доджем на Python")
clock = pg.time.Clock()

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
GREEN = (0, 255, 0)

# Шрифты
title_font = pg.font.SysFont('Tahoma', 72)
menu_font = pg.font.SysFont('Times New Roman', 48)
message_font = pg.font.SysFont('Tahoma', 36)
rules_font = pg.font.SysFont('Tahoma', 23)

# Состояния игры
MENU = 0
GAME = 1
RULES = 2  # Новое состояние для экрана правил
game_state = MENU

# Остальные настройки игры
icon = pg.image.load('icon32.png')
pg.display.set_icon(icon)

# Файл для сохранения
SAVE_FILE = 'dodgem_save.dat'

white_checker = "white-regular.png"
black_checker = "black-regular.png"

# Поле 6x6
board = [
    ["xx", "fb", "fb", "fb", "fb", "xx"],
    ["ww", "--", "--", "--", "--", "fw"],
    ["ww", "--", "--", "--", "--", "fw"],
    ["ww", "--", "--", "--", "--", "fw"],
    ["ww", "--", "--", "--", "--", "fw"],
    ["--", "bb", "bb", "bb", "bb", "xx"]
]

# Переменные для анимации
selected_piece = None
moving_piece = None
animation_speed = 0.1
current_color = "white"
game_over = False
winner = None
save_message_timer = 0

# Загрузка изображений шашек
image_white = pg.image.load(white_checker).convert_alpha()
img_w = pg.transform.smoothscale(image_white, (140, 140))
image_black = pg.image.load(black_checker).convert_alpha()
img_b = pg.transform.smoothscale(image_black, (140, 140))


def check_win_condition():
    """Проверяет условия победы для поля 6x6"""
    black_count = 0
    for col in range(6):
        if board[0][col] == "bb":
            black_count += 1
    if black_count >= 4:
        return "black"

    white_count = 0
    for row in range(6):
        if board[row][5] == "ww":
            white_count += 1
    if white_count >= 4:
        return "white"

    return None


def get_valid_moves(row, col):
    """Возвращает список допустимых ходов для фишки в позиции (row, col)"""
    moves = []

    # Проверяем, достигла ли фишка своего края
    if board[row][col] == "ww" and col == 5:  # Белые фишки в правом столбце
        return []
    if board[row][col] == "bb" and row == 0:  # Чёрные фишки в верхней строке
        return []

    if board[row][col] == "ww":
        directions = [(-1, 0), (0, 1), (1, 0)]
    elif board[row][col] == "bb":
        directions = [(0, -1), (0, 1), (-1, 0)]
    else:
        return moves

    for dr, dc in directions:
        new_row, new_col = row + dr, col + dc
        if 0 <= new_row < 6 and 0 <= new_col < 6:  # Сначала проверяем границы
            cell = board[new_row][new_col]
            if cell == "--" or (current_color == "white" and cell == "fw") or (current_color == "black" and cell == "fb"):
                moves.append((new_row, new_col))

    return moves


def draw_valid_moves(moves):
    """Отрисовывает зеленые кружки на допустимых ходах"""
    for row, col in moves:
        pg.draw.circle(screen, (0, 255, 0), (col * 160 + 80, row * 160 + 80), 15)


def move_piece(start_row, start_col, end_row, end_col):
    """Начинает анимацию перемещения фишки"""
    global moving_piece
    piece_type = board[start_row][start_col]
    board[start_row][start_col] = "--"
    pg.mixer.music.load("sound.mp3")
    pg.mixer.music.play()
    moving_piece = (start_row, start_col, end_row, end_col, 0, piece_type)


def update_animation():
    """Обновляет прогресс анимации"""
    global moving_piece, board, current_color, game_over, winner
    if moving_piece:
        start_row, start_col, end_row, end_col, progress, piece_type = moving_piece
        progress += animation_speed
        if progress >= 1:
            board[end_row][end_col] = piece_type
            moving_piece = None
            winner = check_win_condition()
            if winner:
                game_over = True
            else:
                current_color = "black" if current_color == "white" else "white"
                # почему здесь?
                check_no_valid_moves()  # <-- Добавлено (проверка после смены хода)
        else:
            moving_piece = (start_row, start_col, end_row, end_col, progress, piece_type)


def draw_board():
    """Отрисовывает игровое поле 6x6"""
    for x in range(6):
        for y in range(6):
            if (x == y == 5) or (x == y == 0) or (x == 5 and y == 0):  # Угловые клетки
                pg.draw.rect(screen, (0, 0, 0), (x * 160, y * 160, 160, 160))
            elif (y == 0 and 1 <= x <= 4) or (x == 5 and 1 <= y <= 4):  # Специальные клетки
                if (x + y) % 2 == 0:
                    pg.draw.rect(screen, (89, 87, 87), (x * 160, y * 160, 160, 160))
                else:
                    pg.draw.rect(screen, (61, 56, 56), (x * 160, y * 160, 160, 160))
            elif (x + y) % 2 == 0:
                pg.draw.rect(screen, (241, 217, 181), (x * 160, y * 160, 160, 160))
            else:
                pg.draw.rect(screen, (181, 135, 99), (x * 160, y * 160, 160, 160))


def draw_pieces():
    """Отрисовывает все фишки на доске"""
    for row in range(6):
        for col in range(6):
            if board[row][col] == "ww":
                rect = img_w.get_rect(center=(col * 160 + 80, row * 160 + 80))
                screen.blit(img_w, rect)
            elif board[row][col] == "bb":
                rect = img_b.get_rect(center=(col * 160 + 80, row * 160 + 80))
                screen.blit(img_b, rect)

    if moving_piece:
        start_row, start_col, end_row, end_col, progress, piece_type = moving_piece
        x = start_col * 160 + 80 + (end_col - start_col) * 160 * progress
        y = start_row * 160 + 80 + (end_row - start_row) * 160 * progress

        if piece_type == "ww":
            rect = img_w.get_rect(center=(x, y))
            screen.blit(img_w, rect)
        else:
            rect = img_b.get_rect(center=(x, y))
            screen.blit(img_b, rect)


def draw_game_over():
    """Отрисовывает сообщение о победе"""
    global game_over, selected_piece, moving_piece, current_color, winner, game_state

    if winner == "white":
        result = pyautogui.confirm(text='Победили белые. Начать новую игру?',
                                   title='Игра окончена',
                                   buttons=['OK', 'Cancel'])
    elif winner == "_white":
        result = pyautogui.confirm(text='Нет доступных ходов! Победили белые. Начать новую игру?',
                                   title='Игра окончена',
                                   buttons=['OK', 'Cancel'])
    elif winner == "_black":
        result = pyautogui.confirm(text='Нет доступных ходов! Победили чёрные. Начать новую игру?',
                                   title='Игра окончена',
                                   buttons=['OK', 'Cancel'])
    else:
        result = pyautogui.confirm(text='Победили чёрные. Начать новую игру?',
                                   title='Игра окончена',
                                   buttons=['OK', 'Cancel'])

    if result == "Cancel":
        game_state = MENU
        return

    game_over = False
    selected_piece = None
    moving_piece = None
    current_color = "white"
    game_over = False
    winner = None
    reset_game()


def reset_game():
    """Сбрасывает игру в начальное состояние"""
    global board, selected_piece, moving_piece, current_color, game_over, winner
    board = [
        ["xx", "fb", "fb", "fb", "fb", "xx"],
        ["ww", "--", "--", "--", "--", "fw"],
        ["ww", "--", "--", "--", "--", "fw"],
        ["ww", "--", "--", "--", "--", "fw"],
        ["ww", "--", "--", "--", "--", "fw"],
        ["--", "bb", "bb", "bb", "bb", "xx"]
    ]
    selected_piece = None
    moving_piece = None
    current_color = "white"
    game_over = False
    winner = None


def save_game():
    """Сохраняет текущее состояние игры в файл"""
    global save_message_timer

    game_state = {
        'board': board,
        'current_color': current_color,
        'selected_piece': selected_piece,
        'moving_piece': moving_piece,
        'game_over': game_over,
        'winner': winner
    }

    try:
        with open(SAVE_FILE, 'wb') as f:
            pickle.dump(game_state, f)
        save_message_timer = 120  # Показываем сообщение 2 секунды (при 60 FPS)
        return True
    except Exception as e:
        print(f"Ошибка при сохранении игры: {e}")
        return False


def load_game():
    """Загружает сохраненную игру из файла"""
    global board, current_color, selected_piece, moving_piece, game_over, winner

    if not os.path.exists(SAVE_FILE):
        return False

    try:
        with open(SAVE_FILE, 'rb') as f:
            game_state = pickle.load(f)

        board = game_state['board']
        current_color = game_state['current_color']
        selected_piece = game_state['selected_piece']
        moving_piece = game_state['moving_piece']
        game_over = game_state['game_over']
        winner = game_state['winner']
        return True
    except Exception as e:
        print(f"Ошибка при загрузке игры: {e}")
        return False


def check_no_valid_moves():
    """Проверяет, есть ли у текущего игрока допустимые ходы.
    Если нет — игра заканчивается, и побеждает соперник."""
    global game_over, winner, current_color

    has_valid_moves = False

    for row in range(6):
        for col in range(6):
            # Проверяем только фишки текущего игрока
            if (current_color == "white" and board[row][col] == "ww") or \
               (current_color == "black" and board[row][col] == "bb"):
                moves = get_valid_moves(row, col)
                if moves:  # Если есть хотя бы один допустимый ход
                    has_valid_moves = True
                    break
        if has_valid_moves:
            break

    # Если ходов нет — игра заканчивается, побеждает соперник
    if not has_valid_moves:
        game_over = True
        winner = "_white" if current_color == "white" else "_black"


def draw_save_message():
    """Отрисовывает сообщение о сохранении игры"""
    if save_message_timer > 0:
        message = message_font.render("Игра сохранена!", True, GREEN)
        message_rect = message.get_rect(center=(screen.get_width() // 2, 50))
        screen.blit(message, message_rect)


def draw_menu():
    """Отрисовывает главное меню"""
    screen.fill(BLACK)

    # Название игры
    title = title_font.render("Доджем", True, WHITE)
    title_rect = title.get_rect(center=(screen.get_width() // 2, screen.get_height() // 4))
    screen.blit(title, title_rect)

    # Кнопка "Начать игру"
    start_text = menu_font.render("Начать игру", True, WHITE)
    start_rect = start_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 - 100))
    screen.blit(start_text, start_rect)

    # Кнопка "Правила игры"
    rules_text = menu_font.render("Правила игры", True, WHITE)
    rules_rect = rules_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
    screen.blit(rules_text, rules_rect)

    # Кнопка "Загрузить игру"
    has_save = os.path.exists(SAVE_FILE)
    load_color = WHITE if has_save else GRAY
    load_game_text = menu_font.render("Загрузить игру", True, load_color)
    load_game_rect = load_game_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 100))
    screen.blit(load_game_text, load_game_rect)

    # Кнопка "Выйти из игры"
    exit_text = menu_font.render("Выйти из игры", True, WHITE)
    exit_rect = exit_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 200))
    screen.blit(exit_text, exit_rect)

    return start_rect, rules_rect, load_game_rect, exit_rect


def draw_rules():
    """Отрисовывает экран с правилами игры"""
    screen.fill(BLACK)

    # Заголовок
    title = title_font.render("Правила игры", True, WHITE)
    title_rect = title.get_rect(center=(screen.get_width() // 2, 80))
    screen.blit(title, title_rect)

    # Текст правил
    rules = [
        "Доджем - стратегическая игра для двух игроков.",
        "",
        "Цель игры:",
        "- Белые должны довести 4 фишки до правого края",
        "- Чёрные должны довести 4 фишки до верхнего края",
        "",
        "Правила ходов:",
        "- Белые ходят: вверх, вправо или вниз",
        "- Чёрные ходят: влево, вправо или вверх",
        "- Фишки не могут ходить назад",
        "- Фишки блокируются при достижении своего края",
        "",
        "Победа:",
        "- Первый, кто доведёт 4 фишки до края - побеждает",
        "- Игрок, полностью заперевший шашки противника, проигрывает."
    ]

    # Отрисовка каждой строки правил
    y_offset = 150
    for line in rules:
        if line:  # Если строка не пустая
            text = rules_font.render(line, True, WHITE)
            screen.blit(text, (100, y_offset))
        y_offset += 40

    # Кнопка "Назад"
    back_text = menu_font.render("Назад", True, WHITE)
    back_rect = back_text.get_rect(center=(screen.get_width() // 2, screen.get_height() - 100))
    screen.blit(back_text, back_rect)

    return back_rect


def handle_menu_click(pos, start_rect, rules_rect, load_game_rect, exit_rect):
    """Обрабатывает клики в меню"""
    global game_state, running

    if start_rect.collidepoint(pos):
        game_state = GAME
        reset_game()
    elif rules_rect.collidepoint(pos):
        game_state = RULES  # Переход на экран правил
    elif load_game_rect.collidepoint(pos) and os.path.exists(SAVE_FILE):
        if load_game():
            game_state = GAME
    elif exit_rect.collidepoint(pos):
        running = False


# Главный игровой цикл
running = True
valid_moves = []
while running:
    if game_state == MENU:
        start_rect, rules_rect, load_game_rect, exit_rect = draw_menu()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                handle_menu_click(event.pos, start_rect, rules_rect, load_game_rect, exit_rect)


    elif game_state == RULES:
        back_rect = draw_rules()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                if back_rect.collidepoint(event.pos):
                    game_state = MENU  # Возврат в меню

    elif game_state == GAME:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:  # Обработка ESC
                    game_state = MENU
                    reset_game()
                if event.key == pg.K_s and (pg.key.get_mods() & pg.KMOD_CTRL):
                    save_game()
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                mouse_x, mouse_y = event.pos
                col = mouse_x // 160
                row = mouse_y // 160

                # print(col, row)

                if game_over:
                    draw_game_over()
                elif not moving_piece:
                    if 0 <= row < 6 and 0 <= col < 6:
                        if (current_color == "white" and board[row][col] == "ww") or \
                                (current_color == "black" and board[row][col] == "bb"):
                            selected_piece = (row, col)
                            valid_moves = get_valid_moves(row, col)
                        elif selected_piece and (row, col) in valid_moves:
                            start_row, start_col = selected_piece
                            move_piece(start_row, start_col, row, col)
                            selected_piece = None
                            valid_moves = []
                        else:
                            selected_piece = None
                            valid_moves = []

        update_animation()
        draw_board()

        if selected_piece and not moving_piece and not game_over:
            row, col = selected_piece
            pg.draw.rect(screen, pg.Color("red"), (col * 160, row * 160, 160, 160), 5)
            draw_valid_moves(valid_moves)

        draw_pieces()
        draw_save_message()

        if save_message_timer > 0:
            save_message_timer -= 1

        if game_over:
            draw_game_over()

    pg.display.flip()
    clock.tick(60)

pg.quit()
sys.exit()
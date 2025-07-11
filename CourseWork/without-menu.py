import pygame as pg
import sys
import pyautogui



# pygame settings
pg.init()
screen = pg.display.set_mode((960, 960))  # Размер для поля 6x6 (6*160=960)
pg.display.set_caption("Игра Доджем на Python")
clock = pg.time.Clock()

# game const
white_checker = "white-regular.png"
black_checker = "black-regular.png"

# Поле 6x6
board = [
    ["xx", "fb", "fb", "fb", "fb", "xx"],
    ["ww", "--", "--", "--", "--", "fw"],
    ["ww", "--", "--", "--", "--", "fw"],
    ["ww", "--", "--", "--", "--", "fw"],
    ["ww", "--", "--", "--", "--", "fw"],
    ["xx", "bb", "bb", "bb", "bb", "xx"]
]

# Переменные для анимации
selected_piece = None
moving_piece = None
animation_speed = 0.1
current_color = "white"
game_over = False
winner = None

# Загрузка изображений шашек
image_white = pg.image.load(white_checker).convert_alpha()
img_w = pg.transform.smoothscale(image_white, (140, 140))
image_black = pg.image.load(black_checker).convert_alpha()
img_b = pg.transform.smoothscale(image_black, (140, 140))

# Шрифт для сообщения о победе
font = pg.font.SysFont('Arial', 72)


def check_win_condition():
    """Проверяет условия победы для поля 6x6"""
    # Проверка победы черных (4 из 4 в верхнем ряду)
    black_count = 0
    for col in range(6):
        if board[0][col] == "bb":
            black_count += 1
    if black_count >= 4:  # Для поля 6x6 нужно 4 фишки
        return "black"

    # Проверка победы белых (4 из 4 в правом столбце)
    white_count = 0
    for row in range(6):
        if board[row][5] == "ww":
            white_count += 1
    if white_count >= 4:  # Для поля 6x6 нужно 4 фишки
        return "white"

    return None


def get_valid_moves(row, col):
    """Возвращает список допустимых ходов для фишки в позиции (row, col)"""
    moves = []
    if board[row][col] == "ww":
        directions = [(-1, 0), (0, 1), (1, 0)]
    elif board[row][col] == "bb":
        directions = [(0, -1), (0, 1), (-1, 0)]
    else:
        return moves

    for dr, dc in directions:
        new_row, new_col = row + dr, col + dc
        if (0 <= new_row < 6 and 0 <= new_col < 6 and board[new_row][new_col] == "--"
                or (current_color == "white" and board[new_row][new_col] == "fw")
                or (current_color == "black" and board[new_row][new_col] == "fb")):
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
        else:
            moving_piece = (start_row, start_col, end_row, end_col, progress, piece_type)


def draw_board():
    """Отрисовывает игровое поле 6x6"""
    for x in range(6):
        for y in range(6):
            if (x + y == 5) and (x + y == 0):  # Угловые клетки
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
    global game_over, selected_piece, moving_piece, current_color, winner

    if winner == "white":
        result = pyautogui.confirm(text='Победили белые. Начать новую игру?',
                                   title='Игра окончена',
                                   buttons=['OK', 'Cancel'])
    else:
        result = pyautogui.confirm(text='Победили чёрные. Начать новую игру?',
                                   title='Игра окончена',
                                   buttons=['OK', 'Cancel'])

    # Если пользователь нажал Cancel, не сбрасываем игру
    if result == "Cancel":
        return  # Выходим из функции, не сбрасывая игру

    # Сброс игры только если нажали OK
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
        ["xx", "bb", "bb", "bb", "bb", "xx"]
    ]
    selected_piece = None
    moving_piece = None
    current_color = "white"
    game_over = False
    winner = None


# Main game loop
running = True
valid_moves = []
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos
            col = mouse_x // 160
            row = mouse_y // 160

            if game_over:
                reset_game()
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

    if game_over:
        draw_game_over()

    pg.display.flip()
    clock.tick(60)

pg.quit()
sys.exit()
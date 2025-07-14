import pygame as pg
import sys
import pyautogui
import pickle
import os
import json  # Для сохранения данных пользователей

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
RED = (255, 0, 0)
BLUE = (0, 120, 255)
LIGHT_BLUE = (173, 216, 230)

# Шрифты
title_font = pg.font.SysFont('Tahoma', 72)
menu_font = pg.font.SysFont('Times New Roman', 42)
message_font = pg.font.SysFont('Tahoma', 36)
rules_font = pg.font.SysFont('Tahoma', 23)
input_font = pg.font.SysFont('Arial', 32)

# Состояния игры
MENU = 0
GAME = 1
RULES = 2
LOGIN = 3
REGISTER = 4
game_state = LOGIN  # Начинаем с экрана входа

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



# Файл для сохранения пользователей
USERS_FILE = 'dodgem_users.json'


# Класс для текстового ввода
class TextInput:
    def __init__(self, x, y, width, height, placeholder='', is_password=False):
        self.rect = pg.Rect(x, y, width, height)
        self.text = ''
        self.active = False
        self.placeholder = placeholder
        self.is_password = is_password
        self.color_inactive = pg.Color('lightskyblue3')
        self.color_active = pg.Color('dodgerblue2')
        self.color = self.color_inactive
        self.txt_surface = input_font.render(placeholder, True, (150, 150, 150))

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            # Если пользователь щелкнул по полю ввода
            self.active = self.rect.collidepoint(event.pos)
            # Изменение цвета поля ввода
            self.color = self.color_active if self.active else self.color_inactive
            if self.active and self.text == '':
                self.text = ''
                self.txt_surface = input_font.render('', True, BLACK)

        if event.type == pg.KEYDOWN:
            if self.active:
                if event.key == pg.K_RETURN:
                    return True
                elif event.key == pg.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode

                # Отображение звездочек для пароля
                if self.is_password:
                    display_text = '*' * len(self.text)
                else:
                    display_text = self.text

                self.txt_surface = input_font.render(display_text, True, BLACK)
        return False

    def draw(self, screen):
        # Рисуем поле ввода
        pg.draw.rect(screen, self.color, self.rect, 0)
        pg.draw.rect(screen, BLACK, self.rect, 2)
        # Рисуем текст
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 10))

        # Отображаем плейсхолдер, если текст пустой
        if self.text == '' and not self.active:
            placeholder_surf = input_font.render(self.placeholder, True, (150, 150, 150))
            screen.blit(placeholder_surf, (self.rect.x + 5, self.rect.y + 10))

    def get_text(self):
        return self.text


# Шифрование пароля шифром Цезаря
def caesar_encrypt(text, shift=3):
    result = ""
    for char in text:
        if char.isalpha():
            # Определяем базовый символ в зависимости от регистра
            base = 'a' if char.islower() else 'A'
            # Шифруем символ
            result += chr((ord(char) - ord(base) + shift) % 26 + ord(base))
        else:
            result += char
    return result


# Дешифрование пароля
def caesar_decrypt(text, shift=3):
    return caesar_encrypt(text, -shift)


# Загрузка пользователей из файла
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                users = json.load(f)
                # Дешифруем пароли при загрузке
                for username, data in users.items():
                    data['password'] = caesar_decrypt(data['password'])
                return users
        except:
            return {}
    return {}


# Сохранение пользователей в файл
def save_users(users):
    # Создаем копию для шифрования паролей
    encrypted_users = {}
    for username, data in users.items():
        encrypted_users[username] = {
            'password': caesar_encrypt(data['password'])
        }

    with open(USERS_FILE, 'w') as f:
        json.dump(encrypted_users, f)


# Текущий пользователь
current_user = None

# Создаем поля ввода для экранов логина и регистрации
login_username = TextInput(330, 300, 300, 50, 'Имя пользователя')
login_password = TextInput(330, 400, 300, 50, 'Пароль', is_password=True)
register_username = TextInput(330, 250, 300, 50, 'Имя пользователя')
register_password = TextInput(330, 350, 300, 50, 'Пароль', is_password=True)
register_confirm = TextInput(330, 450, 300, 50, 'Подтвердите пароль', is_password=True)

# Сообщения об ошибках
login_error = ''
register_error = ''

# Загружаем пользователей
users = load_users()


def draw_login_screen():
    """Отрисовывает экран входа"""
    screen.fill(LIGHT_BLUE)

    # Заголовок
    title = title_font.render("Вход в систему", True, BLUE)
    title_rect = title.get_rect(center=(screen.get_width() // 2, 150))
    screen.blit(title, title_rect)

    # Поля ввода
    login_username.draw(screen)
    login_password.draw(screen)

    # Кнопка входа
    login_btn = pg.Rect(380, 500, 200, 60)
    pg.draw.rect(screen, GREEN, login_btn, border_radius=15)
    login_text = menu_font.render("Войти", True, WHITE)
    login_text_rect = login_text.get_rect(center=login_btn.center)
    screen.blit(login_text, login_text_rect)

    # Кнопка регистрации
    register_btn = pg.Rect(330, 600, 300, 60)
    pg.draw.rect(screen, BLUE, register_btn, border_radius=15)
    register_text = menu_font.render("Регистрация", True, WHITE)
    register_text_rect = register_text.get_rect(center=register_btn.center)
    screen.blit(register_text, register_text_rect)

    # Сообщение об ошибке
    if login_error:
        error_text = message_font.render(login_error, True, RED)
        error_rect = error_text.get_rect(center=(screen.get_width() // 2, 580))
        screen.blit(error_text, error_rect)

    return login_btn, register_btn


def draw_register_screen():
    """Отрисовывает экран регистрации"""
    screen.fill(LIGHT_BLUE)

    # Заголовок
    title = title_font.render("Регистрация", True, BLUE)
    title_rect = title.get_rect(center=(screen.get_width() // 2, 150))
    screen.blit(title, title_rect)

    # Поля ввода
    register_username.draw(screen)
    register_password.draw(screen)
    register_confirm.draw(screen)

    # Кнопка регистрации
    register_btn = pg.Rect(280, 550, 400, 60)
    pg.draw.rect(screen, GREEN, register_btn, border_radius=15)
    register_text = menu_font.render("Зарегистрироваться", True, WHITE)
    register_text_rect = register_text.get_rect(center=register_btn.center)
    screen.blit(register_text, register_text_rect)

    # Кнопка назад
    back_btn = pg.Rect(380, 650, 200, 60)
    pg.draw.rect(screen, GRAY, back_btn, border_radius=15)
    back_text = menu_font.render("Назад", True, WHITE)
    back_text_rect = back_text.get_rect(center=back_btn.center)
    screen.blit(back_text, back_text_rect)

    # Сообщение об ошибке
    if register_error:
        error_text = message_font.render(register_error, True, RED)
        error_rect = error_text.get_rect(center=(screen.get_width() // 2, 520))
        screen.blit(error_text, error_rect)

    return register_btn, back_btn


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


# В главном меню добавим отображение текущего пользователя
def draw_menu():
    """Отрисовывает главное меню"""
    screen.fill(BLACK)

    # Отображаем текущего пользователя
    if current_user:
        user_text = message_font.render(f"Пользователь: {current_user}", True, GREEN)
        screen.blit(user_text, (20, 20))

    # Кнопка выхода из аккаунта
    if current_user:
        logout_btn = pg.Rect(700, 20, 240, 40)
        pg.draw.rect(screen, RED, logout_btn, border_radius=10)
        logout_text = rules_font.render("Выйти из аккаунта", True, WHITE)
        logout_rect = logout_text.get_rect(center=logout_btn.center)
        screen.blit(logout_text, logout_rect)
    else:
        logout_btn = None

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

    return start_rect, rules_rect, load_game_rect, exit_rect, logout_btn


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
    if game_state == LOGIN:
        login_btn, register_btn = draw_login_screen()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

            # Обработка ввода текста
            login_username.handle_event(event)
            if login_password.handle_event(event):
                # Если нажат Enter в поле пароля, пытаемся войти
                username = login_username.get_text()
                password = login_password.get_text()

                if username in users and users[username]['password'] == password:
                    current_user = username
                    game_state = MENU
                    login_error = ''
                else:
                    login_error = 'Неверное имя пользователя или пароль'

            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                if login_btn.collidepoint(event.pos):
                    username = login_username.get_text()
                    password = login_password.get_text()

                    if username in users and users[username]['password'] == password:
                        current_user = username
                        game_state = MENU
                        login_error = ''
                    else:
                        login_error = 'Неверное имя пользователя или пароль'

                if register_btn.collidepoint(event.pos):
                    game_state = REGISTER
                    register_error = ''
                    # Сброс полей регистрации
                    register_username.text = ''
                    register_password.text = ''
                    register_confirm.text = ''
                    register_username.txt_surface = input_font.render('', True, BLACK)
                    register_password.txt_surface = input_font.render('', True, BLACK)
                    register_confirm.txt_surface = input_font.render('', True, BLACK)

    elif game_state == REGISTER:
        register_btn, back_btn = draw_register_screen()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

            # Обработка ввода текста
            register_username.handle_event(event)
            register_password.handle_event(event)
            if register_confirm.handle_event(event):
                # Если нажат Enter в поле подтверждения, пытаемся зарегистрироваться
                username = register_username.get_text()
                password = register_password.get_text()
                confirm = register_confirm.get_text()

                if not username:
                    register_error = 'Введите имя пользователя'
                elif username in users:
                    register_error = 'Имя пользователя занято'
                elif not password:
                    register_error = 'Введите пароль'
                elif password != confirm:
                    register_error = 'Пароли не совпадают'
                else:
                    # Регистрируем нового пользователя
                    users[username] = {'password': password}
                    save_users(users)
                    current_user = username
                    game_state = MENU
                    register_error = ''

            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                if register_btn.collidepoint(event.pos):
                    username = register_username.get_text()
                    password = register_password.get_text()
                    confirm = register_confirm.get_text()

                    if not username:
                        register_error = 'Введите имя пользователя'
                    elif username in users:
                        register_error = 'Имя пользователя занято'
                    elif not password:
                        register_error = 'Введите пароль'
                    elif password != confirm:
                        register_error = 'Пароли не совпадают'
                    else:
                        # Регистрируем нового пользователя
                        users[username] = {'password': password}
                        save_users(users)
                        current_user = username
                        game_state = MENU
                        register_error = ''

                if back_btn.collidepoint(event.pos):
                    game_state = LOGIN
                    login_error = ''
                    # Сброс полей логина
                    login_username.text = ''
                    login_password.text = ''
                    login_username.txt_surface = input_font.render('', True, BLACK)
                    login_password.txt_surface = input_font.render('', True, BLACK)

    elif game_state == MENU:
        start_rect, rules_rect, load_game_rect, exit_rect, logout_btn = draw_menu()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if logout_btn and logout_btn.collidepoint(pos):
                    current_user = None
                    game_state = LOGIN
                    # Сброс полей логина
                    login_username.text = ''
                    login_password.text = ''
                    login_username.txt_surface = input_font.render('', True, BLACK)
                    login_password.txt_surface = input_font.render('', True, BLACK)
                elif start_rect.collidepoint(pos):
                    game_state = GAME
                    reset_game()
                elif rules_rect.collidepoint(pos):
                    game_state = RULES
                elif load_game_rect.collidepoint(pos) and os.path.exists(SAVE_FILE):
                    if load_game():
                        game_state = GAME
                elif exit_rect.collidepoint(pos):
                    running = False

    elif game_state == RULES:
        back_rect = draw_rules()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                if back_rect.collidepoint(event.pos):
                    game_state = MENU

    elif game_state == GAME:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    game_state = MENU
                    reset_game()
                if event.key == pg.K_s and (pg.key.get_mods() & pg.KMOD_CTRL):
                    save_game()
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                mouse_x, mouse_y = event.pos
                col = mouse_x // 160
                row = mouse_y // 160

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

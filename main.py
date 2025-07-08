import pygame
from pygame.locals import *
import sys
import time
import random
import os
import json  # New: for saving/loading user data

SCREEN_WIDTH = 1000  # Increased width for more UI elements
SCREEN_HEIGHT = 700  # Increased height
FPS = 60

THEMES = {
    "Dark Mode": {
        "BACKGROUND": (20, 20, 20),  # Deep dark
        "FOREGROUND": (240, 240, 240),  # Bright white
        "SECONDARY": (80, 80, 80),  # Dark gray for subtle elements
        "HIGHLIGHT": (150, 150, 150),  # Light gray for subtle highlights
        "PRIMARY_ACCENT": (30, 144, 255),  # Dodger Blue for buttons/primary focus
        "SECONDARY_ACCENT": (255, 165, 0),  # Vibrant Orange for headings/secondary focus
        "CORRECT_TEXT": (50, 205, 50),  # Lime Green
        "INCORRECT_TEXT": (255, 70, 70),  # Bright Red
        "PROGRESS_BAR": (100, 150, 255),
        "CURSOR": (240, 240, 240),  # White cursor
        "KEYBOARD_NORMAL": (50, 50, 50),
        "KEYBOARD_HIGHLIGHT": (70, 70, 70),
        "KEYBOARD_TEXT": (200, 200, 200),
        "HEATMAP_LOW": (50, 205, 50),  # Green (few errors)
        "HEATMAP_MEDIUM": (255, 255, 0),  # Yellow (medium errors)
        "HEATMAP_HIGH": (255, 0, 0),  # Red (many errors)
    },
    "Light Mode": {
        "BACKGROUND": (240, 240, 240),
        "FOREGROUND": (50, 50, 50),
        "SECONDARY": (180, 180, 180),
        "HIGHLIGHT": (120, 120, 120),
        "PRIMARY_ACCENT": (70, 130, 180),  # Steel Blue
        "SECONDARY_ACCENT": (255, 99, 71),  # Tomato
        "CORRECT_TEXT": (34, 139, 34),  # Forest Green
        "INCORRECT_TEXT": (220, 20, 60),  # Crimson
        "PROGRESS_BAR": (70, 130, 180),
        "CURSOR": (50, 50, 50),
        "KEYBOARD_NORMAL": (200, 200, 200),
        "KEYBOARD_HIGHLIGHT": (180, 180, 180),
        "KEYBOARD_TEXT": (80, 80, 80),
        "HEATMAP_LOW": (34, 139, 34),
        "HEATMAP_MEDIUM": (255, 165, 0),
        "HEATMAP_HIGH": (220, 20, 60),
    }
}
DEFAULT_THEME = "Dark Mode"

MENU = 0
TYPING = 1
RESULTS = 2
PARAGRAPH_SELECT = 3
COUNTDOWN = 4
USER_SELECT = 5  # New state for user management
CREATE_USER = 6  # New state for creating a new user

ASSETS_DIR = 'assets'
AUDIO_DIR = os.path.join(ASSETS_DIR, 'audio')
SENTENCES_FILE = 'sentences.txt'
USERS_FILE = 'users.json'  # New: File to store user data

INPUT_BOX_WIDTH = 700
INPUT_BOX_HEIGHT = 100
INPUT_BOX_X = (SCREEN_WIDTH - INPUT_BOX_WIDTH) // 2
INPUT_BOX_Y = SCREEN_HEIGHT // 2 - 50

PROGRESS_BAR_WIDTH = 600
PROGRESS_BAR_HEIGHT = 20
PROGRESS_BAR_X = (SCREEN_WIDTH - PROGRESS_BAR_WIDTH) // 2
PROGRESS_BAR_Y = SCREEN_HEIGHT - 120

KEYBOARD_LAYOUT = [
    "`1234567890-=",
    "qwertyuiop[]\\",
    "asdfghjkl;'",
    "zxcvbnm,./",
    " "  # Spacebar
]
# Define key positions for drawing (relative to keyboard's top-left)
# This will be calculated dynamically based on font size later for better scaling
KEY_WIDTH = 40
KEY_HEIGHT = 40
KEY_MARGIN = 5



class Button:
    def __init__(self, x, y, width, height, text, font_size, color_name, hover_color_name, text_color_name,
                 game_instance):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, font_size)
        self.color_name = color_name
        self.hover_color_name = hover_color_name
        self.text_color_name = text_color_name
        self.is_hovered = False
        self.game = game_instance  # Reference to game instance for theme colors

    def draw(self, screen):
        current_theme_colors = self.game.current_theme_colors
        current_color = current_theme_colors[self.hover_color_name] if self.is_hovered else current_theme_colors[
            self.color_name]
        pygame.draw.rect(screen, current_color, self.rect, border_radius=8)
        text_surface = self.font.render(self.text, True, current_theme_colors[self.text_color_name])
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False



class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Typing Speed Master')

        self.font_lg = pygame.font.Font(None, 74)
        self.font_md = pygame.font.Font(None, 48)
        self.font_sm = pygame.font.Font(None, 36)
        self.font_xs = pygame.font.Font(None, 24)
        self.font_key = pygame.font.Font(None, 20)  # Font for keyboard keys

        self.current_state = MENU

        self.current_theme_name = DEFAULT_THEME
        self.current_theme_colors = THEMES[DEFAULT_THEME]

        self.users_data = self._load_users_data()
        self.current_user = None  # No user selected initially
        self.new_user_input = ""  # For user creation
        self.user_input_active = False  # For user creation input box

        self.input_text = ""
        self.target_paragraph = ""
        self.time_start = 0
        self.total_time = 0
        self.errors = 0
        self.wpm = 0
        self.accuracy = 0.0

        self.cursor_visible = True
        self.cursor_timer = 0
        self.cursor_blink_rate = 500

        self.input_scroll_offset_x = 0

        self.countdown_number = 3
        self.countdown_start_time = 0

        self.wpm_history = []  # Stores (timestamp, wpm) pairs during typing
        self.error_char_map = {}  # Tracks errors per character {char: count}
        self.last_typed_char_pos = 0  # To calculate omissions/insertions
        self.detailed_errors = {'insertions': 0, 'omissions': 0, 'substitutions': 0}
        self.key_heatmap_data = {}  # {key_char: error_count} for keyboard visualizer
        self.current_key_to_press = ''  # For on-screen keyboard highlighting

        self.paragraphs = self._load_paragraphs()
        self.selected_paragraph_index = 0
        if self.paragraphs:
            self.target_paragraph = self.paragraphs[self.selected_paragraph_index]
        else:
            self.target_paragraph = "No paragraphs loaded. Please check sentences.txt."

        self.start_button = Button(SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 + 80, 240, 60, "Start Typing", 45,
                                   "PRIMARY_ACCENT", "SECONDARY_ACCENT", "FOREGROUND", self)
        self.restart_button = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 50, "Restart", 40,
                                     "PRIMARY_ACCENT", "SECONDARY_ACCENT", "FOREGROUND", self)
        self.select_paragraph_button = Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 160, 300, 60,
                                              "Select Paragraph", 40, "SECONDARY_ACCENT", "PRIMARY_ACCENT",
                                              "FOREGROUND", self)
        self.back_to_menu_button = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 70, 200, 50, "Back to Menu", 35,
                                          "SECONDARY", "HIGHLIGHT", "FOREGROUND", self)
        self.paragraph_buttons = []

        self.manage_users_button = Button(SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 + 240, 240, 60, "Manage Users",
                                          40, "PRIMARY_ACCENT", "SECONDARY_ACCENT", "FOREGROUND", self)
        self.create_user_button = Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 80, 300, 60, "Create New User",
                                         40, "PRIMARY_ACCENT", "SECONDARY_ACCENT", "FOREGROUND", self)
        self.select_user_button = Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 160, 300, 60, "Select User", 40,
                                         "SECONDARY_ACCENT", "PRIMARY_ACCENT", "FOREGROUND", self)
        self.theme_toggle_button = Button(SCREEN_WIDTH - 150, 20, 120, 40, "Toggle Theme", 28, "SECONDARY", "HIGHLIGHT",
                                          "FOREGROUND", self)  # New button for theme

        self.user_selection_buttons = []  # For dynamic user selection buttons

        self.background_img = None
        try:
            self.background_img = pygame.image.load(os.path.join(ASSETS_DIR, 'background.jpg')).convert()
            self.background_img = pygame.transform.scale(self.background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except pygame.error:
            print("Warning: background.jpg not found in assets folder. Using solid color background.")
            self.background_img = None

        self.key_press_sound = self._load_sound(os.path.join(AUDIO_DIR, 'key_press.wav'))
        self.error_sound = self._load_sound(os.path.join(AUDIO_DIR, 'error.wav'))
        self.game_start_sound = self._load_sound(os.path.join(AUDIO_DIR, 'game_start.wav'))
        self.game_complete_sound = self._load_sound(os.path.join(AUDIO_DIR, 'game_complete.wav'))

        self.keyboard_key_rects = {}  # Stores {char: pygame.Rect} for drawing/heatmap

    def _load_sound(self, path):
        try:
            sound = pygame.mixer.Sound(path)
            if "key_press" in path:
                sound.set_volume(0.3)
            return sound
        except FileNotFoundError:
            print(f"Warning: Sound file not found: {path}. Skipping this sound.")
            return None
        except pygame.error as e:
            print(f"Warning: Could not load sound file {path} due to Pygame error: {e}. Skipping this sound.")
            return None

    def _play_sound(self, sound):
        """Plays a sound if it's loaded."""
        if sound:
            sound.play()

    def _load_paragraphs(self):
        """Loads paragraphs from sentences.txt, ensuring each line is a valid paragraph."""
        paragraphs = []
        try:
            with open(SENTENCES_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line:
                        paragraphs.append(stripped_line)
            if not paragraphs:
                print(f"Warning: {SENTENCES_FILE} is empty or contains no valid paragraphs.")
                return ["No paragraphs found. Add some to sentences.txt!"]
            return paragraphs
        except FileNotFoundError:
            print(f"Error: {SENTENCES_FILE} not found. Please create it in the same directory.")
            return ["Error: sentences.txt not found!"]

    def _set_theme(self, theme_name):
        """Sets the current theme for the game."""
        if theme_name in THEMES:
            self.current_theme_name = theme_name
            self.current_theme_colors = THEMES[theme_name]
        else:
            print(f"Warning: Theme '{theme_name}' not found. Reverting to default.")
            self.current_theme_name = DEFAULT_THEME
            self.current_theme_colors = THEMES[DEFAULT_THEME]

    def _load_users_data(self):
        """Loads all user profiles and their typing history from users.json."""
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"No {USERS_FILE} found or file corrupted. Starting with empty user data.")
            return {"users": {}}

    def _save_users_data(self):
        """Saves all user profiles and their typing history to users.json."""
        try:
            with open(USERS_FILE, 'w') as f:
                json.dump(self.users_data, f, indent=4)
        except IOError:
            print(f"Error: Could not save user data to {USERS_FILE}.")

    def _create_user(self, username):
        """Creates a new user profile."""
        if username and username not in self.users_data["users"]:
            self.users_data["users"][username] = {
                "high_wpm": 0,
                "low_wpm": float('inf'),  # Store as inf for proper comparison, handle during display
                "history": []  # List of dicts: {'wpm', 'accuracy', 'time', 'errors', 'paragraph', 'date'}
            }
            self._save_users_data()
            self.current_user = username
            self.current_state = MENU
            print(f"User '{username}' created and selected.")
            return True
        elif username in self.users_data["users"]:
            print(f"User '{username}' already exists.")
            return False
        else:
            print("Username cannot be empty.")
            return False

    def _select_user(self, username):
        """Selects an existing user profile."""
        if username in self.users_data["users"]:
            self.current_user = username
            # Update game's high/low WPM from user's data
            self.high_wpm = self.users_data["users"][username].get("high_wpm", 0)
            self.low_wpm = self.users_data["users"][username].get("low_wpm", float('inf'))
            self.current_state = MENU
            print(f"User '{username}' selected.")
        else:
            print(f"User '{username}' not found.")

    def _update_user_scores(self, wpm, accuracy, total_time, errors, paragraph):
        """Updates the current user's high/low WPM and adds session to history."""
        if not self.current_user:
            return  # Cannot save if no user selected

        user_profile = self.users_data["users"][self.current_user]

        # Update high/low WPM
        if wpm > user_profile["high_wpm"]:
            user_profile["high_wpm"] = wpm
        if wpm < user_profile["low_wpm"] and wpm > 0:
            user_profile["low_wpm"] = wpm

        user_profile["history"].append({
            "wpm": round(wpm),
            "accuracy": round(accuracy, 1),
            "time": round(total_time, 1),
            "errors": errors,
            "paragraph": paragraph[:50] + "..." if len(paragraph) > 50 else paragraph,  # Store snippet
            "date": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        user_profile["history"] = user_profile["history"][-50:]  # Keep last 50 entries

        self._save_users_data()
        # Also update game's internal high/low for display
        self.high_wpm = user_profile["high_wpm"]
        self.low_wpm = user_profile["low_wpm"]

    def _wrap_text(self, text, font, max_width):
        words = text.split(' ')
        wrapped_lines = []
        current_line_words = []

        for word in words:
            test_line = ' '.join(current_line_words + [word])
            if font.size(test_line)[0] > max_width and current_line_words:
                wrapped_lines.append(' '.join(current_line_words))
                current_line_words = [word]
            else:
                current_line_words.append(word)

        if current_line_words:
            wrapped_lines.append(' '.join(current_line_words))

        return wrapped_lines

    def _draw_text_multiline(self, screen, text, font, color, center_x, start_y, max_width=None,
                             line_spacing_factor=1.2, align="center"):
        lines = self._wrap_text(text, font, max_width) if max_width else [text]
        current_y = start_y
        for line in lines:
            text_surface = font.render(line, True, color)
            text_rect = text_surface.get_rect()
            if align == "center":
                text_rect.center = (center_x, current_y)
            elif align == "left":
                text_rect.midleft = (center_x, current_y)  # center_x is actually x_start
            elif align == "right":
                text_rect.midright = (center_x, current_y)  # center_x is actually x_end

            screen.blit(text_surface, text_rect)
            current_y += font.get_linesize() * line_spacing_factor

    def _reset_game(self):
        """Resets game variables and initiates countdown."""
        self.input_text = ""
        self.time_start = 0
        self.total_time = 0
        self.errors = 0
        self.wpm = 0
        self.accuracy = 0.0
        self.input_scroll_offset_x = 0
        self.wpm_history = []
        self.error_char_map = {}
        self.detailed_errors = {'insertions': 0, 'omissions': 0, 'substitutions': 0}
        self.key_heatmap_data = {char: 0 for row in KEYBOARD_LAYOUT for char in row}  # Initialize all keys to 0 errors
        self.last_typed_char_pos = 0  # For error type tracking

        self.target_paragraph = self.paragraphs[self.selected_paragraph_index]
        self.current_key_to_press = self.target_paragraph[0] if self.target_paragraph else ''

        self.countdown_number = 3
        self.countdown_start_time = pygame.time.get_ticks()
        self.current_state = COUNTDOWN

    def _calculate_results(self):
        """Calculates final metrics and transitions to results state."""
        self.total_time = time.time() - self.time_start
        if self.total_time == 0: self.total_time = 0.1

        correct_chars = 0
        for i in range(min(len(self.input_text), len(self.target_paragraph))):
            if self.input_text[i] == self.target_paragraph[i]:
                correct_chars += 1

        self.wpm = (len(self.input_text) / 5) / (self.total_time / 60)


        self.accuracy = (correct_chars / len(self.input_text)) * 100 if len(self.input_text) > 0 else 0.0

        self._update_user_scores(self.wpm, self.accuracy, self.total_time, self.errors, self.target_paragraph)

        self._play_sound(self.game_complete_sound)
        self.current_state = RESULTS

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False

            if self.current_state == MENU:
                if self.start_button.handle_event(event):
                    self._reset_game()
                if self.select_paragraph_button.handle_event(event):
                    self.current_state = PARAGRAPH_SELECT
                    self._create_paragraph_buttons()
                if self.manage_users_button.handle_event(event):
                    self.current_state = USER_SELECT
                    self._create_user_selection_buttons()
                if self.theme_toggle_button.handle_event(event):
                    if self.current_theme_name == "Dark Mode":
                        self._set_theme("Light Mode")
                    else:
                        self._set_theme("Dark Mode")

            elif self.current_state == PARAGRAPH_SELECT:
                for i, btn in enumerate(self.paragraph_buttons):
                    if btn.handle_event(event):
                        self.selected_paragraph_index = i
                        self.target_paragraph = self.paragraphs[self.selected_paragraph_index]
                        self.current_state = MENU
                if self.back_to_menu_button.handle_event(event):
                    self.current_state = MENU

            elif self.current_state == USER_SELECT:
                if self.create_user_button.handle_event(event):
                    self.current_state = CREATE_USER
                    self.new_user_input = ""  # Clear previous input
                    self.user_input_active = True
                for btn in self.user_selection_buttons:
                    if btn.handle_event(event):
                        self._select_user(btn.text)  # Button text is username
                if self.back_to_menu_button.handle_event(event):
                    self.current_state = MENU

            elif self.current_state == CREATE_USER:
                if event.type == KEYDOWN:
                    if event.key == K_BACKSPACE:
                        self.new_user_input = self.new_user_input[:-1]
                    elif event.key == K_RETURN:
                        if self._create_user(self.new_user_input.strip()):
                            self.user_input_active = False
                            # State change handled by _create_user
                        else:
                            # Display error message on screen
                            pass  # For now, just print to console
                    else:
                        if event.unicode and self.font_md.size(self.new_user_input + event.unicode)[
                            0] < INPUT_BOX_WIDTH - 20:
                            self.new_user_input += event.unicode
                if self.back_to_menu_button.handle_event(event):  # Allow backing out
                    self.current_state = USER_SELECT
                    self.user_input_active = False  # Deactivate input

            elif self.current_state == TYPING:
                if event.type == KEYDOWN:
                    self.cursor_timer = pygame.time.get_ticks()
                    self.cursor_visible = True

                    if event.key == K_BACKSPACE:
                        if self.input_text:
                            # If we're deleting an error that was recorded as substitution/insertion
                            # This part is tricky to perfectly undo detailed error counts, simpler to just decrement total_errors
                            self.input_text = self.input_text[:-1]
                            self._play_sound(self.key_press_sound)
                            self.current_key_to_press = self.target_paragraph[len(self.input_text)] if len(
                                self.input_text) < len(self.target_paragraph) else ''
                    elif event.key == K_RETURN:
                        self._calculate_results()
                    elif event.key == K_ESCAPE:
                        self.current_state = MENU
                    else:
                        if event.unicode and len(self.input_text) < len(self.target_paragraph) + 100:
                            typed_char = event.unicode
                            target_char = self.target_paragraph[len(self.input_text)] if len(self.input_text) < len(
                                self.target_paragraph) else ''

                            if typed_char == target_char:
                                self._play_sound(self.key_press_sound)
                            else:
                                self._play_sound(self.error_sound)
                                self.errors += 1  # Increment total errors

                                self.key_heatmap_data[typed_char.lower()] = self.key_heatmap_data.get(
                                    typed_char.lower(), 0) + 1

                                if len(self.input_text) < len(self.target_paragraph):
                                    if typed_char != target_char:
                                        self.detailed_errors['substitutions'] += 1
                                else:  # typed beyond target, so it's an insertion
                                    self.detailed_errors['insertions'] += 1

                            self.input_text += typed_char
                            # Update next key to press
                            self.current_key_to_press = self.target_paragraph[len(self.input_text)] if len(
                                self.input_text) < len(self.target_paragraph) else ''

    def _update_game_state(self):
        current_time_ms = pygame.time.get_ticks()

        if self.current_state == COUNTDOWN:
            elapsed_time_countdown = (current_time_ms - self.countdown_start_time) // 1000
            self.countdown_number = 3 - elapsed_time_countdown
            if self.countdown_number <= 0:
                self.current_state = TYPING
                self.time_start = time.time()
                self._play_sound(self.game_start_sound)

        elif self.current_state == TYPING:
            if self.time_start != 0:
                self.total_time = time.time() - self.time_start

                correct_chars_live = 0
                for i in range(min(len(self.input_text), len(self.target_paragraph))):
                    if self.input_text[i] == self.target_paragraph[i]:
                        correct_chars_live += 1

                if self.total_time > 0:
                    self.wpm = (len(self.input_text) / 5) / (self.total_time / 60)
                    self.accuracy = (correct_chars_live / len(self.input_text)) * 100 if len(
                        self.input_text) > 0 else 0.0

                    if len(self.wpm_history) == 0 or (
                            self.total_time * 1000 - self.wpm_history[-1][0]) >= 1000:  # Every second
                        self.wpm_history.append((self.total_time * 1000, self.wpm))

            if current_time_ms - self.cursor_timer > self.cursor_blink_rate:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = current_time_ms
            typed_surface = self.font_sm.render(self.input_text, True, self.current_theme_colors["FOREGROUND"])
            typed_width = typed_surface.get_width()

            if typed_width > INPUT_BOX_WIDTH - 20:  # 20px padding
                self.input_scroll_offset_x = (INPUT_BOX_WIDTH - 20) - typed_width
            else:
                self.input_scroll_offset_x = 0

            
            self.errors = 0
            for i in range(min(len(self.input_text), len(self.target_paragraph))):
                if self.input_text[i] != self.target_paragraph[i]:
                    self.errors += 1
            self.errors += max(0, len(self.input_text) - len(
                self.target_paragraph))  # Count extra typed characters as errors
            self.errors += max(0, len(self.target_paragraph) - len(self.input_text))

            if self.current_state == RESULTS:  # Only calculate omissions precisely at the end
                omissions_at_end = 0
                if len(self.target_paragraph) > len(self.input_text):
                    # All characters in target beyond input length are omissions
                    omissions_at_end = len(self.target_paragraph) - len(self.input_text)
                self.detailed_errors['omissions'] = omissions_at_end

    # --- UI Drawing Functions ---
    def _draw_ui(self):
        current_colors = self.current_theme_colors
        self.screen.fill(current_colors["BACKGROUND"])
        if self.background_img:
            self.screen.blit(self.background_img, (0, 0))

        # Draw Theme Toggle Button on all main screens
        if self.current_state in [MENU, RESULTS, PARAGRAPH_SELECT, USER_SELECT, CREATE_USER]:
            self.theme_toggle_button.draw(self.screen)

        if self.current_state == MENU:
            self._draw_menu_screen()
        elif self.current_state == PARAGRAPH_SELECT:
            self._draw_paragraph_select_screen()
        elif self.current_state == USER_SELECT:
            self._draw_user_select_screen()
        elif self.current_state == CREATE_USER:
            self._draw_create_user_screen()
        elif self.current_state == COUNTDOWN:
            self._draw_countdown_screen()
        elif self.current_state == TYPING:
            self._draw_typing_screen()
        elif self.current_state == RESULTS:
            self._draw_results_screen()

        pygame.display.flip()

    def _draw_menu_screen(self):
        current_colors = self.current_theme_colors
        self._draw_text_multiline(self.screen, "Typing Speed Master", self.font_lg, current_colors["PRIMARY_ACCENT"],
                                  SCREEN_WIDTH // 2, 100)
        self._draw_text_multiline(self.screen, "Improve your typing skills!", self.font_sm, current_colors["HIGHLIGHT"],
                                  SCREEN_WIDTH // 2, 180)

        # Display Current User
        user_display = self.current_user if self.current_user else "Guest"
        self._draw_text_multiline(self.screen, f"User: {user_display}", self.font_md, current_colors["FOREGROUND"],
                                  SCREEN_WIDTH // 2, 250)

        # Display User's High/Low Scores
        if self.current_user:
            user_profile = self.users_data["users"][self.current_user]
            high_wpm_display = round(user_profile.get("high_wpm", 0))
            low_wpm_display = round(user_profile.get("low_wpm", float('inf'))) if user_profile.get("low_wpm", float(
                'inf')) != float('inf') else 'N/A'
            self._draw_text_multiline(self.screen, f"High WPM: {high_wpm_display}", self.font_sm,
                                      current_colors["FOREGROUND"], SCREEN_WIDTH // 2, 300)
            self._draw_text_multiline(self.screen, f"Low WPM: {low_wpm_display}", self.font_sm,
                                      current_colors["FOREGROUND"], SCREEN_WIDTH // 2, 340)
        else:
            self._draw_text_multiline(self.screen, "Please select or create a user.", self.font_sm,
                                      current_colors["HIGHLIGHT"], SCREEN_WIDTH // 2, 320)

        selected_para_snippet = self.target_paragraph[:70] + "..." if len(
            self.target_paragraph) > 70 else self.target_paragraph
        self._draw_text_multiline(self.screen, f"Selected: '{selected_para_snippet}'", self.font_xs,
                                  current_colors["HIGHLIGHT"], SCREEN_WIDTH // 2, 400)

        self.start_button.draw(self.screen)
        self.select_paragraph_button.draw(self.screen)
        self.manage_users_button.draw(self.screen)  # New button

    def _draw_paragraph_select_screen(self):
        current_colors = self.current_theme_colors
        self._draw_text_multiline(self.screen, "Select a Paragraph", self.font_md, current_colors["PRIMARY_ACCENT"],
                                  SCREEN_WIDTH // 2, 50)

        for btn in self.paragraph_buttons:
            btn.draw(self.screen)

        self.back_to_menu_button.draw(self.screen)

    def _draw_user_select_screen(self):
        current_colors = self.current_theme_colors
        self._draw_text_multiline(self.screen, "Manage Users", self.font_md, current_colors["PRIMARY_ACCENT"],
                                  SCREEN_WIDTH // 2, 50)

        self.create_user_button.draw(self.screen)

        # Draw existing user buttons
        y_offset = SCREEN_HEIGHT // 2 + 240
        if not self.user_selection_buttons:
            self._draw_text_multiline(self.screen, "No users found. Create one!", self.font_sm,
                                      current_colors["HIGHLIGHT"], SCREEN_WIDTH // 2, y_offset)

        for btn in self.user_selection_buttons:
            btn.draw(self.screen)

        self.back_to_menu_button.draw(self.screen)

    def _draw_create_user_screen(self):
        current_colors = self.current_theme_colors
        self._draw_text_multiline(self.screen, "Create New User", self.font_md, current_colors["PRIMARY_ACCENT"],
                                  SCREEN_WIDTH // 2, 100)
        self._draw_text_multiline(self.screen, "Enter Username:", self.font_sm, current_colors["FOREGROUND"],
                                  SCREEN_WIDTH // 2, 200)

        # Input Box for username
        input_rect = pygame.Rect(SCREEN_WIDTH // 2 - INPUT_BOX_WIDTH // 2, 250, INPUT_BOX_WIDTH, 50)
        pygame.draw.rect(self.screen, current_colors["HIGHLIGHT"], input_rect, 2, border_radius=8)

        input_surface = self.font_sm.render(self.new_user_input, True, current_colors["FOREGROUND"])
        self.screen.blit(input_surface,
                         (input_rect.x + 10, input_rect.y + (input_rect.height - input_surface.get_height()) // 2))

        # Blinking cursor for input
        if self.user_input_active and self.cursor_visible:
            cursor_x = input_rect.x + 10 + input_surface.get_width()
            pygame.draw.line(self.screen, current_colors["CURSOR"], (cursor_x, input_rect.y + 10),
                             (cursor_x, input_rect.y + input_rect.height - 10), 2)

        self.back_to_menu_button.draw(self.screen)
        self.back_to_menu_button.rect.y = SCREEN_HEIGHT - 100  # Adjust position for this screen

    def _draw_countdown_screen(self):
        current_colors = self.current_theme_colors
        self._draw_text_multiline(self.screen, "Get Ready!", self.font_md, current_colors["HIGHLIGHT"],
                                  SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100)
        self._draw_text_multiline(self.screen, str(max(0, self.countdown_number)), self.font_lg,
                                  current_colors["PRIMARY_ACCENT"], SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    def _draw_typing_screen(self):
        current_colors = self.current_theme_colors
        self._draw_text_multiline(self.screen, "Type the following paragraph:", self.font_sm,
                                  current_colors["HIGHLIGHT"], SCREEN_WIDTH // 2, 50)

        paragraph_lines = self._wrap_text(self.target_paragraph, self.font_sm, INPUT_BOX_WIDTH)

        current_y_for_para = 120
        total_chars_rendered = 0

        for line_idx, target_line in enumerate(paragraph_lines):
            x_offset = INPUT_BOX_X + (INPUT_BOX_WIDTH - self.font_sm.size(target_line)[0]) // 2
            current_char_x = x_offset

            for i, char in enumerate(target_line):
                char_color = current_colors["HIGHLIGHT"]  # Default color for remaining text

                if total_chars_rendered < len(self.input_text):
                    if self.input_text[total_chars_rendered] == char:
                        char_color = current_colors["CORRECT_TEXT"]
                    else:
                        char_color = current_colors["INCORRECT_TEXT"]

                char_surface = self.font_sm.render(char, True, char_color)
                self.screen.blit(char_surface, (current_char_x, current_y_for_para))
                current_char_x += char_surface.get_width()
                total_chars_rendered += 1

            current_y_for_para += self.font_sm.get_linesize() * 1.2

        # Draw the input box border
        pygame.draw.rect(self.screen, current_colors["PRIMARY_ACCENT"],
                         (INPUT_BOX_X, INPUT_BOX_Y, INPUT_BOX_WIDTH, INPUT_BOX_HEIGHT), 2, border_radius=8)

        input_text_surface = self.font_sm.render(self.input_text, True, current_colors["FOREGROUND"])

        input_clip_rect = pygame.Rect(INPUT_BOX_X + 5, INPUT_BOX_Y + 5, INPUT_BOX_WIDTH - 10, INPUT_BOX_HEIGHT - 10)
        self.screen.set_clip(input_clip_rect)

        self.screen.blit(input_text_surface, (INPUT_BOX_X + 10 + self.input_scroll_offset_x,
                                              INPUT_BOX_Y + (INPUT_BOX_HEIGHT - input_text_surface.get_height()) // 2))

        # Draw Blinking Cursor
        if self.cursor_visible:
            cursor_x = INPUT_BOX_X + 10 + self.input_scroll_offset_x + input_text_surface.get_width()
            cursor_y = INPUT_BOX_Y + (INPUT_BOX_HEIGHT - self.font_sm.get_height()) // 2
            pygame.draw.line(self.screen, current_colors["CURSOR"], (cursor_x, cursor_y),
                             (cursor_x, cursor_y + self.font_sm.get_height()), 2)

        self.screen.set_clip(None)

        # Draw Progress Bar
        progress_percentage = (len(self.input_text) / len(self.target_paragraph)) if len(
            self.target_paragraph) > 0 else 0
        progress_fill_width = PROGRESS_BAR_WIDTH * progress_percentage

        pygame.draw.rect(self.screen, current_colors["SECONDARY"],
                         (PROGRESS_BAR_X, PROGRESS_BAR_Y, PROGRESS_BAR_WIDTH, PROGRESS_BAR_HEIGHT), border_radius=5)
        pygame.draw.rect(self.screen, current_colors["PROGRESS_BAR"],
                         (PROGRESS_BAR_X, PROGRESS_BAR_Y, progress_fill_width, PROGRESS_BAR_HEIGHT), border_radius=5)
        pygame.draw.rect(self.screen, current_colors["FOREGROUND"],
                         (PROGRESS_BAR_X, PROGRESS_BAR_Y, PROGRESS_BAR_WIDTH, PROGRESS_BAR_HEIGHT), 1, border_radius=5)

        # Display Real-time Stats
        self._draw_text_multiline(self.screen, f"Time: {int(self.total_time)}s", self.font_sm,
                                  current_colors["FOREGROUND"], SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT - 80)
        self._draw_text_multiline(self.screen, f"WPM: {int(self.wpm)}", self.font_sm, current_colors["FOREGROUND"],
                                  SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80)
        self._draw_text_multiline(self.screen, f"Acc: {self.accuracy:.1f}%", self.font_sm, current_colors["FOREGROUND"],
                                  SCREEN_WIDTH // 2 + 200, SCREEN_HEIGHT - 80)

        self._draw_on_screen_keyboard()  # Draw the keyboard

    def _draw_on_screen_keyboard(self):
        current_colors = self.current_theme_colors
        keyboard_start_x = (SCREEN_WIDTH - (len(KEYBOARD_LAYOUT[0]) * (KEY_WIDTH + KEY_MARGIN) - KEY_MARGIN)) // 2
        keyboard_start_y = SCREEN_HEIGHT - 280  # Position the keyboard

        # Build key rects if not already done (only once)
        if not self.keyboard_key_rects:
            for r_idx, row in enumerate(KEYBOARD_LAYOUT):
                row_offset_x = 0
                if r_idx == 1:  # QWERTY row offset
                    row_offset_x = KEY_WIDTH // 2
                elif r_idx == 2:  # ASDF row offset
                    row_offset_x = KEY_WIDTH
                elif r_idx == 3:  # ZXCV row offset
                    row_offset_x = KEY_WIDTH * 1.25  # Slightly more offset
                elif r_idx == 4:  # Spacebar
                    row_offset_x = KEY_WIDTH * 2  # Center spacebar roughly

                for c_idx, char in enumerate(row):
                    x = keyboard_start_x + row_offset_x + c_idx * (KEY_WIDTH + KEY_MARGIN)
                    y = keyboard_start_y + r_idx * (KEY_HEIGHT + KEY_MARGIN)
                    # Special handling for spacebar size
                    width = KEY_WIDTH
                    if char == ' ':
                        width = KEY_WIDTH * 6  # Make spacebar wider
                        x = keyboard_start_x + row_offset_x + KEY_WIDTH * 3  # Center spacebar

                    self.keyboard_key_rects[char] = pygame.Rect(x, y, width, KEY_HEIGHT)

        # Draw keys
        for char, rect in self.keyboard_key_rects.items():
            key_color = current_colors["KEYBOARD_NORMAL"]
            text_color = current_colors["KEYBOARD_TEXT"]

            # Highlight next key to press
            if char.lower() == self.current_key_to_press.lower():
                key_color = current_colors["PRIMARY_ACCENT"]

            # Heatmap coloring
            error_count = self.key_heatmap_data.get(char.lower(), 0)
            if error_count > 0:
                if error_count > 5:  # Many errors
                    key_color = current_colors["HEATMAP_HIGH"]
                elif error_count > 2:  # Medium errors
                    key_color = current_colors["HEATMAP_MEDIUM"]
                else:  # Few errors
                    key_color = current_colors["HEATMAP_LOW"]
                text_color = current_colors["FOREGROUND"]  # Make text pop on colored key

            pygame.draw.rect(self.screen, key_color, rect, border_radius=5)
            pygame.draw.rect(self.screen, current_colors["SECONDARY"], rect, 1, border_radius=5)  # Border

            char_display = char.upper() if char.islower() else char  # Display uppercase for letters
            if char == ' ': char_display = "Space"  # Label for spacebar

            text_surface = self.font_key.render(char_display, True, text_color)
            text_rect = text_surface.get_rect(center=rect.center)
            self.screen.blit(text_surface, text_rect)

    def _draw_results_screen(self):
        current_colors = self.current_theme_colors
        self._draw_text_multiline(self.screen, "Results", self.font_lg, current_colors["PRIMARY_ACCENT"],
                                  SCREEN_WIDTH // 2, 50)

        # Main Stats
        self._draw_text_multiline(self.screen, f"WPM: {round(self.wpm)}", self.font_md, current_colors["FOREGROUND"],
                                  SCREEN_WIDTH // 2 - 150, 150)
        self._draw_text_multiline(self.screen, f"Accuracy: {self.accuracy:.1f}%", self.font_md,
                                  current_colors["FOREGROUND"], SCREEN_WIDTH // 2 + 150, 150)
        self._draw_text_multiline(self.screen, f"Total Time: {round(self.total_time)}s", self.font_md,
                                  current_colors["FOREGROUND"], SCREEN_WIDTH // 2, 200)
        self._draw_text_multiline(self.screen, f"Total Errors: {self.errors}", self.font_md,
                                  current_colors["FOREGROUND"], SCREEN_WIDTH // 2, 250)

        # Detailed Errors
        self._draw_text_multiline(self.screen, "Error Breakdown:", self.font_sm, current_colors["HIGHLIGHT"],
                                  SCREEN_WIDTH // 2 - 300, 320, align="left")
        self._draw_text_multiline(self.screen, f"Substitutions: {self.detailed_errors['substitutions']}", self.font_xs,
                                  current_colors["FOREGROUND"], SCREEN_WIDTH // 2 - 300, 350, align="left")
        self._draw_text_multiline(self.screen, f"Insertions: {self.detailed_errors['insertions']}", self.font_xs,
                                  current_colors["FOREGROUND"], SCREEN_WIDTH // 2 - 300, 370, align="left")
        self._draw_text_multiline(self.screen, f"Omissions: {self.detailed_errors['omissions']}", self.font_xs,
                                  current_colors["FOREGROUND"], SCREEN_WIDTH // 2 - 300, 390, align="left")

        # WPM Fluctuations Graph
        self._draw_text_multiline(self.screen, "WPM Fluctuations (WPM vs Time)", self.font_sm,
                                  current_colors["HIGHLIGHT"], SCREEN_WIDTH // 2 + 150, 320, align="center")
        self._draw_wpm_graph(self.screen, SCREEN_WIDTH // 2 + 150, 350, 350, 200)  # Centered x, start y, width, height

        # Draw buttons
        self.restart_button.draw(self.screen)
        self.back_to_menu_button.draw(self.screen)

    def _draw_wpm_graph(self, screen, center_x, start_y, graph_width, graph_height):
        current_colors = self.current_theme_colors
        graph_rect = pygame.Rect(center_x - graph_width // 2, start_y, graph_width, graph_height)
        pygame.draw.rect(screen, current_colors["SECONDARY"], graph_rect, border_radius=5)  # Graph background
        pygame.draw.rect(screen, current_colors["FOREGROUND"], graph_rect, 1, border_radius=5)  # Graph border

        if not self.wpm_history:
            self._draw_text_multiline(screen, "No WPM data", self.font_xs, current_colors["HIGHLIGHT"],
                                      graph_rect.centerx, graph_rect.centery)
            return

        # Determine max WPM and max time for scaling
        max_wpm = max([w for _, w in self.wpm_history]) if self.wpm_history else 1
        max_time_ms = self.wpm_history[-1][0] if self.wpm_history else 1

        if max_wpm < 50: max_wpm = 50  # Ensure y-axis doesn't get too compressed for low WPM
        if max_time_ms < 1000: max_time_ms = 1000  # Ensure x-axis for very short tests

        points = []
        for time_ms, wpm in self.wpm_history:
            # Map time to x-coordinate (0 to graph_width)
            x = graph_rect.x + (time_ms / max_time_ms) * graph_width
            # Map WPM to y-coordinate (graph_height to 0, inverted for drawing)
            y = graph_rect.y + graph_height - (wpm / max_wpm) * graph_height
            points.append((x, y))

        if len(points) > 1:
            pygame.draw.lines(screen, current_colors["PRIMARY_ACCENT"], False, points, 2)
        elif len(points) == 1:
            pygame.draw.circle(screen, current_colors["PRIMARY_ACCENT"], points[0], 3)  # Draw a single point

        # Draw Y-axis label (WPM)
        self._draw_text_multiline(screen, "WPM", self.font_xs, current_colors["HIGHLIGHT"], graph_rect.x - 20,
                                  graph_rect.centery, align="right")
        # Draw X-axis label (Time)
        self._draw_text_multiline(screen, "Time (s)", self.font_xs, current_colors["HIGHLIGHT"], graph_rect.centerx,
                                  graph_rect.y + graph_height + 15)

    # --- Dynamic Button Creation ---
    def _create_paragraph_buttons(self):
        self.paragraph_buttons = []
        y_offset = 120
        # Limit paragraph display to fit screen, or add scrolling if many
        display_limit = int((SCREEN_HEIGHT - y_offset - self.back_to_menu_button.rect.height - 30) / (55))
        for i, para in enumerate(self.paragraphs[:display_limit]):
            btn_text = f"P{i + 1}: {para[:60]}..." if len(para) > 60 else f"P{i + 1}: {para}"
            btn = Button(
                SCREEN_WIDTH // 2 - 300, y_offset, 600, 45,
                btn_text, 28, "SECONDARY", "HIGHLIGHT", "FOREGROUND", self
            )
            self.paragraph_buttons.append(btn)
            y_offset += 55

    def _create_user_selection_buttons(self):
        self.user_selection_buttons = []
        y_offset = SCREEN_HEIGHT // 2 + 160  # Below the "Select User" button

        users = list(self.users_data["users"].keys())

        if not users:
            return  # No users to make buttons for

        # Sort users alphabetically
        users.sort()

        # Limit number of users displayed on screen for readability
        display_limit = int((SCREEN_HEIGHT - y_offset - self.back_to_menu_button.rect.height - 30) / (55))

        for i, user_name in enumerate(users[:display_limit]):
            btn = Button(
                SCREEN_WIDTH // 2 - 150, y_offset, 300, 45,
                user_name, 30, "SECONDARY", "HIGHLIGHT", "FOREGROUND", self
            )
            self.user_selection_buttons.append(btn)
            y_offset += 55

    def run(self):
        self.running = True
        clock = pygame.time.Clock()

        # Initial theme setup
        self._set_theme(DEFAULT_THEME)

        while self.running:
            self._handle_events()
            self._update_game_state()
            self._draw_ui()
            clock.tick(FPS)

        pygame.quit()
        sys.exit()


# --- Main execution block ---
if __name__ == '__main__':
    game = Game()
    game.run()

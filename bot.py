import time
import pyautogui
from pathlib import Path
from PIL import ImageGrab
import numpy as np
import cv2
from tkinter import *
from multiprocessing import Queue
import config


class Bot:
    def __init__(self, queue: Queue, parameters: dict, debug_mode: bool):
        self.queue = queue
        self.parameters = parameters
        self.debug_mode = debug_mode

    def logging(self, data) -> None:
        f = open('temp.txt', 'w')
        f.write(f'{data}\n')
        f.close()

    def getTemplates(self, folder_name: str) -> dict:
        # сами шаблоны и их размеры в пикселях в формате:{'file_name':(img_template, (width, height))}
        templates = {}
        files = Path.cwd().glob(f'{folder_name}\\*.png')

        for file_name in files:
            file_name_str = str(file_name)
            img_template = cv2.imread(file_name_str, cv2.IMREAD_GRAYSCALE)
            templates[file_name_str] = (img_template, img_template.shape[::-1])

        return templates

    def findTemplates(self, templates: dict, screen_area: dict) -> tuple[int, int, int, int]:
        # x,y найденного верхнего угла шаблона + ширина и высота самого шаблона
        result = (0, 0, 0, 0)
        base_screen_file = 'screenshot.png'
        base_screen = ImageGrab.grab(bbox=(
            screen_area['x1'], screen_area['y1'], screen_area['x2'], screen_area['y2']))
        base_screen.save(base_screen_file)

        for path in templates:
            img_template = templates[path][0]
            wt, ht = templates[path][1]
            # я думаю тут можно считать не файл, а поток в памяти для скорости
            img_screen_original = cv2.imread(base_screen_file)
            img_screen_gray = cv2.cvtColor(
                img_screen_original, cv2.COLOR_BGR2GRAY)
            res = cv2.matchTemplate(
                img_screen_gray, img_template, cv2.TM_CCOEFF_NORMED)
            # массив областей-кандидатов в поплавки
            loc = np.where(res > self.parameters['threshold'])

            if self.debug_mode:
                for pt in zip(*loc[::-1]):
                    cv2.rectangle(img_screen_original, pt,
                                  (pt[0] + wt, pt[1] + ht), (0, 0, 255), 2)
                cv2.imshow('Найдено', img_screen_original)
                cv2.waitKey(0)

            if np.any(loc[0]):
                # if self.debug_mode:
                #    cv2.imwrite('Templates\\session_' + str(int(time.time())) + '_success.png', img_rgb)
                self.queue.put((END, f'Найден шаблон: {path}\n'))
                result = (loc[1][0], loc[0][0], wt, ht)
                break

        return result

    def start_fishing(self) -> None:
        current_time = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime())
        self.queue.put((END, f'Начали процесс рыбалки: {current_time}\n'))
        templates = self.getTemplates(config.TEMPLATES_FISH)

        diff_list = []  # Список средних разностей величин от пикселей скриншота
        # mean_diff = 0  # Средняя разность величин для поиска шаблона поплавка на скриншоте
        time.sleep(2)

        for iteration in range(self.parameters['iterations']):
            # Сообщение для окна бота в виде кортежа (координаты, текст)
            self.queue.put((END, f'Заброс удочки № {iteration}\n'))

            if self.debug_mode:
                self.logging(self.queue.qsize())

            previous_average_mean = 0  # средняя величина разностей величин от пикселей скриншота
            pyautogui.moveTo(self.parameters['start_button_x'],
                             self.parameters['start_button_y'])  # тут координаты нашей кнопки с забрасыванием удочки
            pyautogui.click(button='left')
            time.sleep(2)
            screen_area = self.parameters['screen_area']['screen_area_fish']
            start_index = 0

            for _ in range(40):
                # примерно 25 секунд = 1 цикл рыбалки
                time.sleep(config.FREQUENCY_FISH)
                result = self.findTemplates(templates, screen_area)

                if not any(result):
                    continue

                width, height, wt, ht = result
                clean_screen = ImageGrab.grab(
                    bbox=(width, height, width + wt, height + ht))
                mean = np.mean(clean_screen)
                # тут уже поплавок найден
                diff = abs(previous_average_mean - mean)
                diff_list.append(diff)
                # mean_diff - Средняя разность всех величин diff для поиска шаблона поплавка на скриншоте
                mean_diff = np.mean(diff_list)

                # определим стартовый индекс для каждого заброса, в этом индексе всегда аномально большое значение, 
                # его каждый 5-й поиск приравниваем к среднему значению что бы не портил статистику
                if _ == 0:
                    start_index = len(diff_list) - 1

                if len(diff_list) % 5:
                    diff_list[start_index] = mean_diff * 10

                self.queue.put(
                    (END, f'diff: {diff}, mean_diff: {mean_diff}\n'))

                if not self.debug_mode and previous_average_mean > 0 and diff > mean_diff:
                    self.queue.put((END, 'КЛЮЕТ!\n'))
                    # pyautogui.moveTo(width + wt / 2, height + ht / 2)
                    pyautogui.moveTo(width + 200, height + ht / 2)
                    pyautogui.click(button='left')
                    time.sleep(1)
                    break

                previous_average_mean = mean

    # дает КС в каст по таргету если пиксель черный или по фокусу если пиксель белый
    def start_kickcast(self) -> None:
        current_time = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime())
        self.queue.put((END, f'Начали процесс автокика: {current_time}\n'))
        button_pressed = False

        while True:
            time.sleep(config.FREQUENCY_KICKCAST)
            pixel_white = pyautogui.pixelMatchesColor(0, 0, (0, 0, 0))
            pixel_black = pyautogui.pixelMatchesColor(0, 0, (255, 255, 255))

            if pixel_white:
                pyautogui.hotkey('shift', 'c')
                button_pressed = True
            elif pixel_black:
                pyautogui.press('c')
                button_pressed = True
            elif button_pressed:
                # тут нажать кнопку отмены заклинания (или пета в пассив режим)
                pyautogui.hotkey('ctrl', '0')
                button_pressed = False

import glob
import time
import pyautogui
from PIL import ImageGrab
import numpy as np
import cv2
from tkinter import *
from tkinter import messagebox
from multiprocessing import Process, Queue, freeze_support

#iterations = 100 количество циклов рыбалки (забросов)
#threshold = 0.65 65% соответствие нашему шаблону для поиска
#limit_of_diff = 10-20 критерий поклевки (коэффициент разности скринов при дергании шаблона)
#screen_area = {'x1': 0, 'y1': 0, 'x2':1600, 'y2':500} область для поиска поплавка
#start_button_x, start_button_y координаты кнопки на экране для запуска рыбалки

class WindowBot:
    def __init__(self, master, queue, debug_mode):
        self.name_program = 'WoW Fishing Bot'
        self.master = master
        self.queue = queue
        self.debug_mode = debug_mode
        self.process_bot = None
        self.master.geometry('720x400')
        self.master.title(self.name_program)
        self.master.protocol('WM_DELETE_WINDOW', self.Exit)

        main_menu = Menu(self.master)
        self.master.config(menu=main_menu)
        help_menu = Menu(main_menu, tearoff=0)
        help_menu.add_command(label='Справка по боту', command=self.GetHelp)
        help_menu.add_command(label='О программе', command=self.GetInfoAboutBot)
        main_menu.add_cascade(label='Справка', menu=help_menu)
        
        self.frame_top = Frame(self.master)
        self.frame_top.pack(side=TOP, fill=X, expand=NO)
        self.frame_label_entry = LabelFrame(self.frame_top, bd=3, text='Параметры:')
        self.frame_label_entry.pack(side=LEFT, fill=X, expand=NO)
        self.frame_label = Frame(self.frame_label_entry)
        self.frame_label.pack(side=LEFT, expand=NO)
        self.frame_entry = Label(self.frame_label_entry)
        self.frame_entry.pack(side=LEFT, expand=NO)
        self.frame_button = Frame(self.frame_top)
        self.frame_button.pack(side=LEFT, expand=NO)
        self.frame_info = LabelFrame(self.master, bd=3, text='Текущее состояние')
        self.frame_info.pack(side=BOTTOM, fill=BOTH, expand=YES)
        
        self.label_iterations = Label(self.frame_label, text='Количество забросов:')
        self.label_iterations.pack(side=TOP)
        self.label_threshold = Label(self.frame_label, text='Коэффициент соответствия шаблонам (0-1):')
        self.label_threshold.pack(side=TOP)
        #self.label_limit_of_diff = Label(self.frame_label, text='Коэффициент влияющий на реакцию бота при дергании поплавка(устарело):')
        #self.label_limit_of_diff.pack(side=TOP)
        self.label_start_button_x = Label(self.frame_label, text='Координата X кнопки рыбалки:')
        self.label_start_button_x.pack(side=TOP)
        self.label_start_button_y = Label(self.frame_label, text='Координата Y кнопки рыбалки:')
        self.label_start_button_y.pack(side=TOP)

        self.iterations = StringVar()
        self.threshold = StringVar()
        #self.limit_of_diff = StringVar()
        self.start_button_x = StringVar()
        self.start_button_y = StringVar()
        
        self.entry_iterations = Entry(self.frame_entry, bd=2, textvariable=self.iterations)
        self.entry_iterations.pack(side=TOP)
        self.entry_threshold = Entry(self.frame_entry, bd=2, textvariable=self.threshold)
        self.entry_threshold.pack(side=TOP)
        #self.entry_limit_of_diff = Entry(self.frame_entry, bd=2, textvariable=self.limit_of_diff)
        #self.entry_limit_of_diff.pack(side=TOP)
        self.entry_start_button_x = Entry(self.frame_entry, bd=2, textvariable=self.start_button_x)
        self.entry_start_button_x.pack(side=TOP)
        self.entry_start_button_y = Entry(self.frame_entry, bd=2, textvariable=self.start_button_y)
        self.entry_start_button_y.pack(side=TOP)

        self.start_button = Button(self.frame_button, bd=2, text='Start', font='arial 16', command=self.Start)
        self.start_button.pack(side=TOP, pady=10)
        self.stop_button = Button(self.frame_button, bd=2, text='Stop', font='arial 16', command=self.Stop)
        self.stop_button.pack(side=TOP)

        self.text_info = Text(self.frame_info, wrap=WORD)
        self.text_info.pack(side=TOP, fill=BOTH, expand=YES)

        self.scroll_text_info = Scrollbar(self.text_info, command=self.text_info.yview)
        self.scroll_text_info.pack(side=RIGHT, fill=Y)
        self.text_info.config(yscrollcommand = self.scroll_text_info.set)

        self.parameters = self.GetParameters()

        if self.parameters:
            self.entry_iterations.insert(1, int(self.parameters['iterations']))
            self.entry_threshold.insert(1, self.parameters['threshold'])
            #self.entry_limit_of_diff.insert(1, self.parameters['limit_of_diff'])
            self.entry_start_button_x.insert(1, int(self.parameters['start_button_x']))
            self.entry_start_button_y.insert(1, int(self.parameters['start_button_y']))
        
        self.master.mainloop()

    def GetInfoAboutBot(self):
        messagebox.showinfo(self.name_program, '"' + self.name_program + '"' + ' powered by Hassan Smirnov(с) 2020')

    def GetHelp(self):
        messagebox.showinfo(self.name_program, 'Скоро напишу короткую справку по работе бота, хотя и так все понятно =)')

    def GetAreaForScreenshot(self):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        screen_area = {'x1': 0, 'y1': 0, 'x2':int(screen_width * 0.8), 'y2':int(screen_height * 0.5)} # область для поиска поплавка
        return screen_area
        
    def GetParameters(self):
        parameters = {}
        fparams = open("ParametersBot.txt", 'r')
        parameters['screen_area'] = self.GetAreaForScreenshot()
        
        for fline in fparams:
            if fline[0] == '#':
                continue
            line = fline.strip().split(':')
            if line[0].replace('_', '').isalpha() and line[1].replace('.', '').isdigit():
                value = float(line[1].strip())
                if value.is_integer():
                    value = int(value)
                parameters[line[0].strip()] = value
            else:
                messagebox.showerror('Ошибка', 'Ошибка при чтении файла параметров: слева нарушены названия параметров или справа не только числа!')
                parameters = {}
                break

        fparams.close()
        return parameters

    def GetParametersFromWindow(self):
        parameters = {}
        parameters['iterations'] = self.iterations.get()
        parameters['threshold'] = self.threshold.get()
        #parameters['limit_of_diff'] = self.limit_of_diff.get()
        parameters['start_button_x'] = self.start_button_x.get()
        parameters['start_button_y'] = self.start_button_y.get()
        
        for key in parameters:
            if not parameters[key].replace('.', '').strip().isdigit():
                messagebox.showerror('Ошибка', 'Ошибка при чтении параметров из окна программы: в параметрах должны быть только цифры!')
                parameters = {}
                break
            else:
                value = float(parameters[key].strip())
                if value.is_integer():
                    value = int(value)
                parameters[key] = value
        
        if parameters:
            parameters['screen_area'] = self.GetAreaForScreenshot()
        
        return parameters

    def GetInfoFromBot(self):
        while not self.queue.empty():
            msg = self.queue.get()
            self.text_info.insert(msg[0], msg[1])
            self.text_info.see(END)
        self.master.after(500, self.GetInfoFromBot)
            
    def Start(self):
        self.parameters = self.GetParametersFromWindow()
        if not self.parameters:
            return
        self.text_info.delete('0.0', END)
        self.start_button.configure(state=DISABLED)
        self.process_bot = ProcessBot(self.queue, self.parameters, self.debug_mode)
        self.process_bot.start()
        self.GetInfoFromBot()
    
    def Stop(self):
        if self.process_bot:
            self.text_info.insert(END, 'Бот остановлен!\n')
            self.process_bot.terminate()
            self.process_bot.join()
            self.process_bot.close()
            self.process_bot = None
        else:
            self.text_info.insert(END, 'Бот остановлен!\n')
        self.start_button.configure(state=NORMAL)

    def Exit(self):
        if self.process_bot:
            self.process_bot.terminate()
            self.process_bot.join()
            self.process_bot.close()
        self.master.destroy()

class Bot:
    def __init__(self, queue, parameters, debug_mode):
        self.queue = queue
        self.parameters = parameters
        self.debug_mode = debug_mode

    def Logging(self, data):
        f = open('temp.txt', 'w')
        f.write(str(data)+'\n')
        f.close()
 
    def GetTemplates(self):
        templates = {} #сами шаблоны и их размеры в пикселях в формате:{'file_name':(img_template, (width, height))}
        files = glob.glob('Templates\\*.png')
        
        for file_name in files:
            img_template = cv2.imread(file_name, cv2.IMREAD_GRAYSCALE)
            templates[file_name] = (img_template, img_template.shape[::-1])
        return templates
    
    def FindTemplates(self, templates):
        result = (0, 0, 0, 0) #x,y найденного верхнего угла шаблона + ширина и высота самого шаблона
        screen_area = self.parameters['screen_area']
        base_screen_file = 'screenshot.png'
        base_screen = ImageGrab.grab(bbox=(screen_area['x1'], screen_area['y1'], screen_area['x2'], screen_area['y2']))
        base_screen.save(base_screen_file)
        for key in templates:
            img_template = templates[key][0]
            wt, ht = templates[key][1]
            img_screen_original = cv2.imread(base_screen_file)
            img_screen_gray = cv2.cvtColor(img_screen_original, cv2.COLOR_BGR2GRAY)
            res = cv2.matchTemplate(img_screen_gray, img_template, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res > self.parameters['threshold'])
            
            if self.debug_mode:
                for pt in zip(*loc[::-1]):
                    cv2.rectangle(img_screen_original, pt, (pt[0]+wt, pt[1]+ht), (0,0,255), 2)
                cv2.imshow('Найдено', img_screen_original)
                cv2.waitKey(0)
                    
            if any(loc[0]):
                #if self.debug_mode:
                #    cv2.imwrite('Templates\\session_' + str(int(time.time())) + '_success.png', img_rgb)
                self.queue.put((END, 'Найден шаблон: ' + key + '\n'))
                result = (loc[1][0], loc[0][0], wt, ht)
                break
            
        return result

    def StartBot(self):
        current_time = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime())
        self.queue.put((END, 'Начали процесс: ' + current_time + '\n'))
        templates = self.GetTemplates()
        
        diff_list = [] #Список средних разностей величин от точек скриншота
        mean_diff = 0 # средняя разность величин поиска поплавка
        time.sleep(2)
        
        for iteration in range(self.parameters['iterations']):
            self.queue.put((END, 'Заброс удочки № ' + str(iteration) + '\n')) #сообщение для окна бота в виде кортежа (координаты, текст)
            if self.debug_mode:
                self.Logging(self.queue.qsize())
            previous_average_mean = 0 # средняя величина от массива точек скриншота
            pyautogui.moveTo(self.parameters['start_button_x'], self.parameters['start_button_y']) #тут координаты нашей кнопки с забрасыванием удочки
            pyautogui.click(button='left')
            time.sleep(2)
            
            for tick in range(32):
                time.sleep(0.5) # примерно 20 секунд = 1 цикл рыбалки
                result = self.FindTemplates(templates)
                if not any(result):
                    continue
                width, height, wt, ht = result
                clean_screen = ImageGrab.grab(bbox=(width, height, width+wt, height+ht))
                mean = np.mean(clean_screen)
                diff = abs(previous_average_mean - mean) # тут уже поплавок найден
                diff_list.append(diff)
                mean_diff = np.mean(diff_list)
                self.queue.put((END, 'diff: {} - mean_diff: {}\n'.format(str(diff), str(mean_diff))))
            
                if not self.debug_mode and previous_average_mean > 0 and diff > mean_diff:
                    self.queue.put((END, 'КЛЮЕТ!\n'))
                    pyautogui.moveTo(width+wt/2, height+ht/2)
                    pyautogui.click(button='left')
                    time.sleep(1)
                    break
                
                previous_average_mean = mean

class ProcessBot(Process):
    def __init__(self, queue, parameters, debug_mode):
        Process.__init__(self)
        self.queue = queue
        self.parameters = parameters
        self.debug_mode = debug_mode
        
    def run(self):
        bot = Bot(self.queue, self.parameters, self.debug_mode)
        bot.StartBot()
        
debug_mode = False

if __name__ == '__main__':
    freeze_support()
    root = Tk()
    mpqueue = Queue()
    WindowBot(root, mpqueue, debug_mode)
    mpqueue.close()
    mpqueue.join_thread()

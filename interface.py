from cmath import exp
from tkinter import *
from tkinter import messagebox
from processes import Queue, ProcessBot
import config

# iterations = 100 количество циклов рыбалки (забросов)
# threshold = 0.65 65% соответствие нашему шаблону для поиска
# limit_of_diff = 10-20 критерий поклевки (коэффициент разности скринов при дергании шаблона)
# screen_area = {'x1': 0, 'y1': 0, 'x2':1600, 'y2':500} область для поиска поплавка
# start_button_x, start_button_y координаты кнопки на экране для запуска рыбалки


class WindowBot:
    def __init__(self, master: Tk, queue: Queue, debug_mode: bool):
        self.name_program = 'WoW Fishing Bot'
        self.master = master
        self.queue = queue
        self.debug_mode = debug_mode
        self.process_bot = None
        self.master.geometry('720x400')
        self.master.title(self.name_program)
        self.master.protocol('WM_DELETE_WINDOW', self.exit)

        main_menu = Menu(self.master)
        self.master.config(menu=main_menu)
        help_menu = Menu(main_menu, tearoff=0)
        help_menu.add_command(label='Справка по боту', command=self.showHelp)
        help_menu.add_command(label='О программе',
                              command=self.showInfoAboutBot)
        main_menu.add_cascade(label='Справка', menu=help_menu)

        # Фрейм верхнего уровня для параметров рыбалки
        self.frame_top_fish = Frame(self.master)
        self.frame_top_fish.pack(side=TOP, fill=X, expand=NO)

        self.frame_label_entry = LabelFrame(
            self.frame_top_fish, bd=3, text='Параметры для рыбалки:')
        self.frame_label_entry.pack(side=LEFT, fill=X, expand=NO)
        self.frame_label = Frame(self.frame_label_entry)
        self.frame_label.pack(side=LEFT, expand=NO)
        self.frame_entry = Label(self.frame_label_entry)
        self.frame_entry.pack(side=LEFT, expand=NO)
        self.frame_button_fish = Frame(self.frame_top_fish)
        self.frame_button_fish.pack(side=LEFT, expand=NO)
        self.frame_info = LabelFrame(
            self.master, bd=3, text='Текущее состояние')
        self.frame_info.pack(side=BOTTOM, fill=BOTH, expand=YES)

        self.label_iterations = Label(
            self.frame_label, text='Количество забросов:')
        self.label_iterations.pack(side=TOP)
        self.label_threshold = Label(
            self.frame_label, text='Коэффициент соответствия шаблонам (0-1):')
        self.label_threshold.pack(side=TOP)
        self.label_start_button_x = Label(
            self.frame_label, text='Координата X кнопки рыбалки:')
        self.label_start_button_x.pack(side=TOP)
        self.label_start_button_y = Label(
            self.frame_label, text='Координата Y кнопки рыбалки:')
        self.label_start_button_y.pack(side=TOP)

        self.iterations = StringVar()
        self.threshold = StringVar()
        self.start_button_x = StringVar()
        self.start_button_y = StringVar()

        self.entry_iterations = Entry(
            self.frame_entry, bd=2, textvariable=self.iterations)
        self.entry_iterations.pack(side=TOP)
        self.entry_threshold = Entry(
            self.frame_entry, bd=2, textvariable=self.threshold)
        self.entry_threshold.pack(side=TOP)
        self.entry_start_button_x = Entry(
            self.frame_entry, bd=2, textvariable=self.start_button_x)
        self.entry_start_button_x.pack(side=TOP)
        self.entry_start_button_y = Entry(
            self.frame_entry, bd=2, textvariable=self.start_button_y)
        self.entry_start_button_y.pack(side=TOP)

        self.start_button_fish = Button(
            self.frame_button_fish, bd=2, text='Start fishing', font='arial 16', command=self.start_fishing)
        self.start_button_fish.pack(side=TOP, pady=10)
        self.stop_button_fish = Button(
            self.frame_button_fish, bd=2, text='Stop fishing', font='arial 16', command=self.stop_fishing)
        self.stop_button_fish.pack(side=TOP)

        # фрейм верхнего уровня для сбития каста
        self.frame_top_kickcast = Frame(self.master)
        self.frame_top_kickcast.pack(side=TOP, fill=X, expand=NO)

        self.frame_label_kickcast = LabelFrame(
            self.frame_top_kickcast, bd=3, text='Авто сбитие каста')
        self.frame_label_kickcast.pack(side=LEFT, fill=BOTH, expand=NO)

        self.kickcast_info = Label(
            self.frame_label_kickcast, text=f'Сбитие каста сканирует вражеские способности с частотой {config.FREQUENCY_KICKCAST}сек.\n Также следует учитывать пинг до сервера')
        self.kickcast_info.pack(side=LEFT, fill=BOTH, expand=NO)

        self.frame_button_kickcast = Frame(self.frame_top_kickcast)
        self.frame_button_kickcast.pack(side=LEFT, expand=NO)

        self.start_button_kickcast = Button(
            self.frame_button_kickcast, bd=2, text='Start autokick', font='arial 16', command=self.start_kickcast)
        self.start_button_kickcast.pack(side=TOP, pady=10)
        self.stop_button_kickcast = Button(
            self.frame_button_kickcast, bd=2, text='Stop autokick', font='arial 16', command=self.stop_kickcast)
        self.stop_button_kickcast.pack(side=TOP)

        self.text_info = Text(self.frame_info, wrap=WORD)
        self.text_info.pack(side=TOP, fill=BOTH, expand=YES)

        self.scroll_text_info = Scrollbar(
            self.text_info, command=self.text_info.yview)
        self.scroll_text_info.pack(side=RIGHT, fill=Y)
        self.text_info.config(yscrollcommand=self.scroll_text_info.set)

        self.parameters = self.getParameters()

        if self.parameters:
            self.entry_iterations.insert(1, int(self.parameters['iterations']))
            self.entry_threshold.insert(1, self.parameters['threshold'])
            self.entry_start_button_x.insert(
                1, int(self.parameters['start_button_x']))
            self.entry_start_button_y.insert(
                1, int(self.parameters['start_button_y']))

        self.master.mainloop()

    def showInfoAboutBot(self) -> None:
        messagebox.showinfo(self.name_program, '"' + self.name_program +
                            '"' + ' powered by Hasan Smirnov(с) 2022')

    def showHelp(self) -> None:
        messagebox.showinfo(self.name_program,
                            'Скоро напишу короткую справку по работе бота, хотя и так все понятно =)')

    def getAreaForScreenshot(self) -> dict:
        screen_area = {}
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        screen_area['screen_area_fish'] = {
            'x1': int(screen_width * 0.1),
            'y1': 0,
            'x2': int(screen_width * 0.8),
            'y2': int(screen_height * 0.5)
        }  # область для поиска поплавка
        screen_area['screen_area_target'] = {
            'x1': int(screen_width * 0.1),
            'y1': 0,
            'x2': int(screen_width * 0.3),
            'y2': int(screen_height * 0.2)
        }  # область для поиска каста цели
        screen_area['screen_area_focus'] = {
            'x1': int(screen_width * 0.1),
            'y1': int(screen_height * 0.2),
            'x2': int(screen_width * 0.3),
            'y2': int(screen_height * 0.4)
        }  # область для поиска каста фокуса

        return screen_area

    def getParameters(self) -> dict:
        parameters = {}
        fparams = open(config.FILE_PARAMETERS, 'r')
        parameters['screen_area'] = self.getAreaForScreenshot()
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
                messagebox.showerror('Ошибка',
                                     'Ошибка при чтении файла параметров: слева нарушены названия параметров или справа не только числа!')
                parameters = {}
                break

        fparams.close()
        return parameters

    def getParametersFromWindow(self) -> dict:
        parameters = {}
        parameters['iterations'] = self.iterations.get()
        parameters['threshold'] = self.threshold.get()
        parameters['start_button_x'] = self.start_button_x.get()
        parameters['start_button_y'] = self.start_button_y.get()

        for key in parameters:
            if not parameters[key].replace('.', '').strip().isdigit():
                messagebox.showerror('Ошибка',
                                     'Ошибка при чтении параметров из окна программы: в параметрах должны быть только цифры!')
                parameters = {}
                break
            else:
                value = float(parameters[key].strip())
                if value.is_integer():
                    value = int(value)
                parameters[key] = value

        if parameters:
            parameters['screen_area'] = self.getAreaForScreenshot()

        return parameters

    def getInfoFromBot(self) -> None:
        while not self.queue.empty():
            msg = self.queue.get()
            self.text_info.insert(msg[0], msg[1])
            self.text_info.see(END)

        self.master.after(500, self.getInfoFromBot)

    def start_fishing(self) -> None:
        self.parameters = self.getParametersFromWindow()

        if not self.parameters:
            return

        self.text_info.delete('0.0', END)
        self.start_button_fish.configure(state=DISABLED)
        self.process_bot = ProcessBot(
            self.queue,
            self.parameters,
            config.ACTION_FISH,
            self.debug_mode
        )
        self.process_bot.start()
        self.getInfoFromBot()

    def stop_fishing(self) -> None:
        if self.process_bot:
            self.text_info.insert(END, 'Рыбалка остановлена!\n')
            self.process_bot.terminate()
            self.process_bot.join()
            self.process_bot.close()
            self.process_bot = None
        else:
            self.text_info.insert(END, 'Рыбалка остановлена!\n')

        self.start_button_fish.configure(state=NORMAL)

    def start_kickcast(self) -> None:
        self.text_info.delete('0.0', END)
        self.start_button_kickcast.configure(state=DISABLED)
        self.process_bot = ProcessBot(
            self.queue,
            self.parameters,
            config.ACTION_KICKCAST,
            self.debug_mode
        )
        self.process_bot.start()
        self.getInfoFromBot()

    def stop_kickcast(self) -> None:
        if self.process_bot:
            self.text_info.insert(END, 'Бот остановлен!\n')
            self.process_bot.terminate()
            self.process_bot.join()
            self.process_bot.close()
            self.process_bot = None
        else:
            self.text_info.insert(END, 'Бот остановлен!\n')

        self.start_button_kickcast.configure(state=NORMAL)

    def exit(self) -> None:
        if self.process_bot:
            self.process_bot.terminate()
            self.process_bot.join()
            self.process_bot.close()

        self.master.destroy()

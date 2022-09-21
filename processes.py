from multiprocessing import Process, Queue, freeze_support
from bot import Bot


class ProcessBot(Process):
    def __init__(self, queue, parameters, debug_mode):
        Process.__init__(self)
        self.queue = queue
        self.parameters = parameters
        self.debug_mode = debug_mode

    def run(self):
        bot = Bot(self.queue, self.parameters, self.debug_mode)
        bot.start()

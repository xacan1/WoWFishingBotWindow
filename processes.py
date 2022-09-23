from multiprocessing import Process, Queue, freeze_support
from bot import Bot
import config


class ProcessBot(Process):
    def __init__(self, queue: Queue, parameters: dict, action: str, debug_mode: bool):
        Process.__init__(self)
        self.queue = queue
        self.parameters = parameters
        self.action = action
        self.debug_mode = debug_mode

    def run(self):
        bot = Bot(self.queue, self.parameters, self.debug_mode)

        if self.action == config.ACTION_FISH:
            bot.start_fishing()
        elif self.action == config.ACTION_KICKCAST:
            bot.start_kickcast()

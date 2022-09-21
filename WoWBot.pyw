from processes import *
from interface import *
import config


if __name__ == '__main__':
    freeze_support()
    root = Tk()
    mpqueue = Queue()
    WindowBot(root, mpqueue, config.DEBUG_MODE)
    mpqueue.close()
    mpqueue.join_thread()

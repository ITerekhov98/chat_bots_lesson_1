import telegram

from environs import Env

env = Env()
env.read_env()

bot = telegram.Bot(token=env.str('TG_TOKEN'))

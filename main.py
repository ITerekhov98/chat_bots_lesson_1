import time
import logging

import requests
import telegram
from environs import Env
from requests.exceptions import ReadTimeout, ConnectionError

from bot_answer_templates import title, fail_status, success_status


logger = logging.getLogger('tg_bot')

class TelegramLogsHandler(logging.Handler):

    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


def fetch_checks(devman_token, timestamp):
    url = 'https://dvmn.org/api/long_polling/'
    headers = {
        'Authorization': f'Token {devman_token}',
    }
    params = {'timestamp': timestamp}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def pooling_devman_api(devman_token, tg_chat_id, bot, timestamp=None):
    failed_connections = 0
    while True:
        try:
            check_detail = fetch_checks(devman_token, timestamp)
        except ReadTimeout:
            logger.exception(err)
            continue
        except ConnectionError:
            logger.exception(err)
            failed_connections += 1
            if failed_connections > 10:
                time.sleep(180)
            continue
        except Exception as err:
            logger.exception(err)
            time.sleep(120)
            continue

        if not check_detail:
            continue

        failed_connections = 0
        if not check_detail['status'] == 'found':
            timestamp = check_detail.get('timestamp_to_request')
            continue

        timestamp = check_detail.get('last_attempt_timestamp')
        lesson_title = check_detail['new_attempts'][0]['lesson_title']
        lesson_url = check_detail['new_attempts'][0]['lesson_url']

        message = f"{title} '{lesson_title}' \r\n\r\n"
        if check_detail['new_attempts'][0]['is_negative']:
            message += fail_status
        else:
            message += success_status
        message += f"\r\n {lesson_url}"
        bot.send_message(
            text=message,
            chat_id=tg_chat_id)


def main():
    env = Env()
    env.read_env()
    bot = telegram.Bot(token=env.str('TG_TOKEN'))
    devman_token = env.str('DEVMAN_API_TOKEN')
    tg_chat_id = env.str('TG_CHAT_ID')

    logger.setLevel(logging.WARNING)
    logger.addHandler(TelegramLogsHandler(bot, tg_chat_id))
    pooling_devman_api(
        devman_token=devman_token,
        tg_chat_id=tg_chat_id,
        bot=bot,
    )



if __name__ == '__main__':
    main()

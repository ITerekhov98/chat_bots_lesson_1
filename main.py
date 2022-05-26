import time 

import requests
import telegram
from environs import Env
from requests.exceptions import ReadTimeout, ConnectionError


from bot_answer_templates import title, fail_status, success_status


def fetch_checks(devman_token, timestamp):
    url = 'https://dvmn.org/api/long_polling/'
    headers = {
        'Authorization': f'Token {devman_token}',
    }
    params = {'timestamp': timestamp}
    response = requests.get(url, headers=headers, params=params, timeout=2)
    response.raise_for_status()
    return response.json()


def pooling_devman_api(devman_token, tg_chat_id, bot, timestamp=5):
    failed_connections = 0
    while True:
        try:
            check_detail = fetch_checks(devman_token, timestamp)
        except ReadTimeout:
            continue
        except ConnectionError:
            failed_connections += 1
            if failed_connections > 10:
                time.sleep(180)
            continue

        if  not check_detail:
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
    pooling_devman_api(
        devman_token=devman_token,
        tg_chat_id=tg_chat_id,
        bot=bot,
    )


if __name__ == '__main__':
    main()

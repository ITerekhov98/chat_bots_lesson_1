import requests

from environs import Env
from requests.exceptions import ReadTimeout, ConnectionError

from tg_bot import bot
from bot_answer_templates import title, fail_status, success_status


def fetch_list_checks(devman_token, timestamp):
    url = 'https://dvmn.org/api/long_polling/'
    headers = {
        'Authorization': f'Token {devman_token}',
    }
    params = {}
    if timestamp:
        params['timestamp'] = timestamp
    try:
        response = requests.get(url, headers=headers, params=params)
    except (ReadTimeout, ConnectionError):
        return
    response.raise_for_status()
    return response.json()


def pooling_devman_api(func, devman_token, tg_chat_id, timestamp=None):
    while True:
        check_detail = func(devman_token, timestamp)
        if check_detail:
            print(check_detail)
            if check_detail['status'] == 'found':
                timestamp = check_detail.get('last_attempt_timestamp')
                lesson_title = check_detail['new_attempts'][0]['lesson_title']
                lesson_url = check_detail['new_attempts'][0]['lesson_url']

                message = f"{title} '{lesson_title}' \r\n\r\n"
                if bool(check_detail['new_attempts'][0]['is_negative']):
                    message += fail_status
                else:
                    message += success_status
                message += f"\r\n {lesson_url}"
                bot.send_message(
                    text=message,
                    chat_id=tg_chat_id)
            else:
                timestamp = check_detail.get('timestamp_to_request')


def main():
    env = Env()
    env.read_env()
    devman_token = env.str('DEVMAN_API_TOKEN')
    tg_chat_id = env.str('TG_CHAT_ID')
    pooling_devman_api(
        func=fetch_list_checks,
        devman_token=devman_token,
        tg_chat_id=tg_chat_id
    )


if __name__ == '__main__':
    main()

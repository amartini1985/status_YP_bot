from http import HTTPStatus

import logging
import os
import requests
import time

from dotenv import load_dotenv
from telebot import TeleBot

from exceptions import TokenUnavailableError, StatusError

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def check_tokens():
    """Проверка доступность переменных окружения."""
    if (
        PRACTICUM_TOKEN is None
        or TELEGRAM_TOKEN is None
        or TELEGRAM_CHAT_ID is None
        or ENDPOINT is None
        or HEADERS is None
    ):
        raise TokenUnavailableError('Ошибка переменных окружения')


def send_message(bot, message):
    """Функция отправляет сообщение в Telegram-чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as error:
        logging.error(f'Ошибка передачи сообщений в Telegram bot: {error}')
    else:
        logging.debug('Сообщение доставлено')


def get_api_answer(timestamp):
    """Функция делает запрос к единственному эндпоинту API-сервиса."""
    try:
        check_tokens()
    except TokenUnavailableError as error:
        logging.critical(f'Ошибка переменных окружения: {error}')
        exit()
    else:
        payload = {'from_date': timestamp}
        try:
            response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        except Exception as error:
            logging.error(f'Ошибка при запросе к основному API: {error}')
        else:
            if response.status_code != HTTPStatus.OK:
                raise StatusError('Отсутствие данных в ответе')
            return response.json()


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Возращаемый тип данных отличен от dict')
    elif 'homeworks' not in response or 'current_date' not in response:
        raise ValueError(
            'Отсутствие ключей "homeworks" и "current_date" в ответе'
        )
    elif not isinstance(response['homeworks'], list):
        raise TypeError('Возращаемый тип данных отличен от list')
    else:
        return True


def parse_status(homework):
    """Вывод информации о конкретной домашней работе."""
    if 'homework_name' not in homework:
        raise ValueError('Отсутствие ключа "homework_name"')
    elif 'status' not in homework:
        raise ValueError('Отсутствие ключа "status"')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError('Недокументированный статус домашней работы"')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логикика программы."""
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    message_error = ''
    while True:
        try:
            answer = get_api_answer(timestamp)
            if check_response(answer):
                if len(answer['homeworks']) == 0:
                    logging.debug('Изменений в статусе работ нет')
                else:
                    for homework in answer['homeworks']:
                        send_message(bot, parse_status(homework))
            timestamp = answer['current_date']
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if message != message_error:
                logging.error(message)
                send_message(bot, message)
                message_error = message
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()

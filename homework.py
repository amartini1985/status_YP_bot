import logging
import os
import sys
import time
from contextlib import suppress
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telebot import TeleBot, apihelper

from exceptions import StatusError

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

TOKENS = (
    'PRACTICUM_TOKEN',
    'TELEGRAM_TOKEN',
    'TELEGRAM_CHAT_ID',
    'ENDPOINT',
    'HEADERS'
)

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

HOMEWORK_NUMBER = 0  # Индекс единственной домашней работы в списке


def check_tokens():
    """Проверка доступность переменных окружения."""
    missing_token = [tokin for tokin in TOKENS if not globals()[tokin]]
    if missing_token:
        message = f'Ошибка переменных окружения {missing_token}'
        logging.critical(message)
        raise ValueError(message)
    logging.debug('Все переменные окружения доступны')


def send_message(bot, message):
    """Отправка сообщений в Telegram-чат."""
    logging.debug('Попытка отправки сообщения')
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    logging.debug('Сообщение доставлено')


def get_api_answer(timestamp):
    """Запрос к эндпоинту API-сервиса."""
    logging.debug('Запрос к эндпойнту')
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException as error:
        param_error = (
            f'URL: {ENDPOINT}, заголовок: {HEADERS}, время: {payload}'
        )
        raise ConnectionError(
            f'Ошибка при запросе к основному API: {error}, ' + param_error
        )
    if response.status_code != HTTPStatus.OK:
        raise StatusError(
            f'Отсутствие данных: {response.status_code}, ' + param_error
        )
    logging.debug('Запрос к эндпойнту - успешен')
    return response.json()


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    logging.debug('Начало проверки ответа API')
    if not isinstance(response, dict):
        raise TypeError(
            f'Возращаемый тип данных отличен от dict - {type(response)}'
        )
    if 'homeworks' not in response:
        raise KeyError(
            'Отсутствие ключей "homeworks" в ответе'
        )
    homework = response['homeworks']
    if not isinstance(homework, list):
        raise TypeError(
            f'Возращаемый тип данных отличен от list - {type(homework)})'
        )
    logging.debug('Проверка ответа API - успешно')


def parse_status(homework):
    """Вывод информации о конкретной домашней работе."""
    logging.debug('Начало вывода информации о работе')
    if 'homework_name' not in homework:
        raise KeyError('Отсутствие ключа "homework_name"')
    if 'status' not in homework:
        raise KeyError('Отсутствие ключа "status"')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError(
            f'Недокументированный статус работы - {homework_status}"'
        )
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логикика программы."""
    check_tokens()
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    message_error = ''
    while True:
        try:
            answer = get_api_answer(timestamp)
            check_response(answer)
            homeworks = answer['homeworks']
            if not homeworks:
                logging.debug('Изменений в статусе работ нет')
                continue
            send_message(bot, parse_status(homeworks[HOMEWORK_NUMBER]))
            timestamp = answer.get('current_date', timestamp)
        except (
            apihelper.ApiException,
            requests.exceptions.RequestException
        ) as error:
            logging.error(
                f'Ошибка при попытке отправить сообщение в ТГ - {error}'
            )
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.exception(message)
            if message != message_error:
                with suppress(Exception):
                    send_message(bot, message)
                    message_error = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[logging.StreamHandler(stream=sys.stdout),],
        format='%(asctime)s - %(name)s - %(levelname)s - '
        '%(funcName)s - %(message)s'
    )
    main()

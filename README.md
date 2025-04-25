
# Описание проекта:

Telegram-бот, который обращается к API сервиса Практикум Домашка и узнет статус домашней работы: взята ли ваша домашка в ревью, проверена ли она, а если проверена — принял её ревьюер или вернул на доработку.

## Используемый стек технологий:
- Python 3.9

## Порядок развертывания проекта:
1) Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:amartini1985/status_YP_bot.git
```

```
cd status_YP_bot

```

2) Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

* Если у вас Linux/macOS

    ```
    source env/bin/activate
    ```

* Если у вас windows

    ```
    source env/scripts/activate
    ```

```
python3 -m pip install --upgrade pip
```

3) Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

4) Запустить файл: homework.py


## Автор проекта:
[Andrey Martyanov/amartini1985](https://github.com/amartini1985)

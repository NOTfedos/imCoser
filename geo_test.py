from flask import Flask, request
import logging
import json
from random import choice


app = Flask(__name__)

# Добавляем логирование в файл
logging.basicConfig(level=logging.INFO, filename='app.log',
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')


# создаём словарь, где для каждого пользователя мы будем хранить информацию о ходе теста
sessionStorage = {}
# Этап работы теста, 1 - выбор уровня сложности, 2 - навык показывает картинку, 3 - игрок отгадывает
difs = ["легко", "средне", "тяжело"]


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Request: %r', response)
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']

    # Если новый пользователь
    if req['session']['new']:
        res['response']['text'] = \
            'Привет! Я могу протестировать тебя по географии!' \
            'Выбери уровень сложности'
        res['response']['buttons'] = [
            {'title': 'Легко', 'hide': True},
            {'title': 'Средне', 'hide': True},
            {'title': 'Тяжело', 'hide': True}
        ]

        sessionStorage[user_id]['stage'] = 1
        sessionStorage[user_id]['good_ans'] = 0
        sessionStorage[user_id]['ticks'] = 0
        sessionStorage[user_id]['skip_ans'] = 0
        sessionStorage[user_id]['difficulty'] = None
        return

    # Если пользователь выбирает уровень сложности
    if sessionStorage[user_id]['stage'] == 1:
        if not req['request']['original_utterance'].lower() in difs:
            res['response']['text'] = \
                'Выбери уровень сложности, это пригодится'
            res['response']['buttons'] = [
                {'title': 'Легко', 'hide': True},
                {'title': 'Средне', 'hide': True},
                {'title': 'Тяжело', 'hide': True}
            ]
            return

        sessionStorage[user_id]['difficulty'] = difs.index(req['request']['original_utterance'].lower())
        sessionStorage[user_id]['stage'] = 2

    # Показываем картинку объекта
    if sessionStorage[user_id]['stage'] == 2:
        correct = choice(geobjs[sessionStorage[user_id]['difficulty']].keys())

        res['response']['text'] = \
            'Тут должна быть картинка'
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['image_id'] = geobjs[correct]

        sessionStorage[user_id]['stage'] = 3
        sessionStorage[user_id]['correct'] = correct
        sessionStorage[user_id]['ticks'] += 1

        return

    # Обрабатываем ответ пользователя
    if sessionStorage[user_id]['stage'] == 3:
        # Если пользователь хочет пропустить объект
        if req['request']['original_utterance'].lower() == 'пропустить':
            res['response']['text'] = \
                'Не надо отчаиваться, в следующий раз повезёт!'
            sessionStorage[user_id]['skip_ans'] += 1
            sessionStorage[user_id]['stage'] = 2
            return

        # Если пользователь хочет снова увидеть картинку объекта
        if 'показать' in req['request']['original_utterance'].lower():
            res['response']['text'] = \
                'Тут должна быть картинка'
            res['response']['card'] = {}
            res['response']['card']['type'] = 'BigImage'
            res['response']['card']['image_id'] = geobjs[sessionStorage[user_id]['correct']]
            return

        # Если пользователь хочет сменить уровень сложности
        if 'сменить' in req['request']['original_utterance'].lower():
            pass

        # Если ответ правильный, то продолжаем тест
        if req['request']['original_utterance'].lower() == sessionStorage[user_id]['correct']:
            res['response']['text'] = \
                'Правильный ответ!'
            sessionStorage[user_id]['good_ans'] += 1
            sessionStorage[user_id]['stage'] = 2
            return
        else:
            res['response']['text'] = \
                'Ответ неверный, попробуйте еще раз'
            res['response']['buttons'] = [
                {'title': 'Пропустить', 'hide': True},
                {'title': 'Показать еще раз', 'hide': True},
            ]
            return


# Загрузка объектов из файла
def load_geo():
    pass


if __name__ == '__main__':
    geobjs = load_geo()
    app.run()

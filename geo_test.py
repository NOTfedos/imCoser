from flask import Flask, request
import logging
import json
from random import choice
import traceback
import os


app = Flask(__name__)

# Добавляем логирование в файл
logging.basicConfig(level=logging.INFO, filename='app.log',
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')


# создаём словарь, где для каждого пользователя мы будем хранить информацию о ходе теста
sessionStorage = {}
# Этап работы теста:
# 1 - выбор уровня сложности
# 2 - навык показывает картинку
# 3 - игрок отгадывает, навык ждет ответа
# 4 - навык на паузе
difs = ["легко", "средне", "сложно"]


# Загрузка объектов из файла
def load_geo():
    path = os.path.join(os.getcwd(), 'Samples', 'geodata.dat')
    # f = open(path, mode='r')
    # dat = f.read()
    geo = [
        {'москва': "965417/7b6365f3876c1291d491"},
        {'москва': "965417/7b6365f3876c1291d491"},
        {'москва': "965417/7b6365f3876c1291d491"}
    ]
    return geo


geobjs = load_geo()


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
    try:
        handle_dialog(response, request.json)
    except Exception as e:
        traceback.print_exc()
    logging.info('Request: %r', response)
    return json.dumps(response)


def handle_dialog(res, req):
    global geobjs
    user_id = req['session']['user_id']

    # Если новый пользователь
    if req['session']['new']:

        res['response']['text'] = \
            'Привет! Я могу протестировать тебя по географии!' \
            'Выбери уровень сложности'

        res['response']['buttons'] = [
            {'title': 'Легко', 'hide': True},
            {'title': 'Средне', 'hide': True},
            {'title': 'Сложно', 'hide': True}
        ]

        sessionStorage[user_id] = {
            'stage': 1,
            'good_ans': 0,
            'ticks': 0,
            'skip_ans': 0,
            'difficulty': 1,
            'ingame': False,
            'correct': None,
            'image_id': None,
            'shown': []
        }

        return

    # Если пользователь выбирает уровень сложности
    if sessionStorage[user_id]['stage'] == 1:
        # Если ответ пользователь это НЕ уровень сложности
        if not req['request']['original_utterance'].lower() in difs:
            res['response']['text'] = \
                '''Выбери уровень сложности, это пригодится (имеется "легко", "средне" и "сложно")'''
            res['response']['buttons'] = [
                {'title': 'Легко', 'hide': True},
                {'title': 'Средне', 'hide': True},
                {'title': 'Сложно', 'hide': True}
            ]
            return

        # Если ответ - это выбранный уровень сложности
        sessionStorage[user_id]['difficulty'] = difs.index(req['request']['original_utterance'].lower())
        res['response']['text'] = 'Успешно установлен уровень сложности: {}'.format(
            req['request']['original_utterance'].lower())

        sessionStorage[user_id]['stage'] = 4

        res['response']['buttons'] = [
            {'title': 'Начать тест', 'hide': True},
            {'title': 'Сменить уровень сложности', 'hide': True},
            {'title': 'Показать свои результаты', 'hide': True}
        ]
        return

    # Если пользователь в процессе тестирования
    if sessionStorage[user_id]['ingame']:

        # Если навык должен показывать картинку
        if sessionStorage[user_id]['stage'] == 2:
            sessionStorage[user_id]['correct'], sessionStorage[user_id]['image_id'] = get_obj(
                geobjs,
                sessionStorage[user_id]
            )
            if sessionStorage[user_id]['correct'] is not None:
                res = display(res, sessionStorage[user_id])
                sessionStorage[user_id]['stage'] = 3
                sessionStorage[user_id]['ticks'] += 1
                return
            else:
                res['response']['text'] = 'У меня закончились тесты :(, попробуйте сменить уровень сложности'
                sessionStorage[user_id]['stage'] = 4
                sessionStorage[user_id]['ingame'] = False
                res['response']['buttons'] = [
                    {'title': 'Начать тест', 'hide': True},
                    {'title': 'Сменить уровень сложности', 'hide': True},
                    {'title': 'Показать свои результаты', 'hide': True}
                ]
                return

        # Если пользователь должен отгадывать
        if sessionStorage[user_id]['stage'] == 3:

            # Если пользователь хочет пропустить объект
            if req['request']['original_utterance'].lower() == 'пропустить':
                res['response']['text'] = \
                    'Не надо отчаиваться, в следующий раз повезёт!'
                sessionStorage[user_id]['skip_ans'] += 1
                res['response']['buttons'] = [
                    {'title': 'Пропустить', 'hide': True},
                    {'title': 'Показать еще раз', 'hide': True},
                    {'title': 'пауза', 'hide': True}
                ]
                sessionStorage[user_id]['correct'], sessionStorage[user_id]['image_id'] = get_obj(
                    geobjs,
                    sessionStorage[user_id]
                )
                if sessionStorage[user_id]['correct'] is not None:
                    res = display(res, sessionStorage[user_id])
                    sessionStorage[user_id]['stage'] = 3
                    return
                else:
                    res['response']['text'] = 'У меня закончились тесты :(, попробуйте сменить уровень сложности'
                    sessionStorage[user_id]['stage'] = 4
                    sessionStorage[user_id]['ingame'] = False
                    res['response']['buttons'] = [
                        {'title': 'Начать тест', 'hide': True},
                        {'title': 'Сменить уровень сложности', 'hide': True},
                        {'title': 'Показать свои результаты', 'hide': True}
                    ]
                    return

            # Если пользователь хочет снова увидеть картинку объекта
            if 'показать' in req['request']['original_utterance'].lower():
                res = display(res, sessionStorage[user_id])
                return

            # Если пользователь хочет сменить уровень сложности
            if req['request']['original_utterance'].lower().startswith('сменить уровень сложности'):
                try:
                    sessionStorage[user_id]['difficulty'] = difs.index(
                        req['request']['original_utterance'].lower().split()[-1])
                except ValueError:
                    res['response']['text'] = 'Доступно: легко, средне и сложно'
                    sessionStorage[user_id]['stage'] = 1
                    return
                res['response']['text'] = 'Вы успешно сменили уровень сложности на {}'.format(
                    difs[sessionStorage[user_id]['difficulty']]
                )
                sessionStorage[user_id]['ticks'] -= 1

                sessionStorage[user_id]['correct'], sessionStorage[user_id]['image_id'] = get_obj(
                    geobjs,
                    sessionStorage[user_id]
                )
                if sessionStorage[user_id]['correct'] is not None:
                    res = display(res, sessionStorage[user_id])
                    sessionStorage[user_id]['stage'] = 3
                    sessionStorage[user_id]['ticks'] += 1
                    return
                else:
                    res['response']['text'] = 'У меня закончились тесты :(, попробуйте сменить уровень сложности'
                    sessionStorage[user_id]['stage'] = 4
                    sessionStorage[user_id]['ingame'] = False
                    res['response']['buttons'] = [
                        {'title': 'Начать тест', 'hide': True},
                        {'title': 'Сменить уровень сложности', 'hide': True},
                        {'title': 'Показать свои результаты', 'hide': True}
                    ]
                    return

            # Если пользователь хочет приостановить тест
            if req['request']['original_utterance'].lower() in [
                'пауза',
                'приостановить',
                'остановить'
            ]:
                sessionStorage[user_id]['ingame'] = False
                sessionStorage[user_id]['ticks'] -= 1
                sessionStorage[user_id]['stage'] = 4
                res['response']['buttons'] = [
                    {'title': 'Начать тест', 'hide': True},
                    {'title': 'Сменить уровень сложности', 'hide': True},
                    {'title': 'Показать свои результаты', 'hide': True}
                ]
                res['response']['text'] = 'Тест приостановлен'
                return

            # Если ответ правильный, то продолжаем тест
            if req['request']['original_utterance'].lower() == sessionStorage[user_id]['correct']:
                res['response']['text'] = \
                    'Правильный ответ!'
                sessionStorage[user_id]['good_ans'] += 1
                sessionStorage[user_id]['stage'] = 3
                sessionStorage[user_id]['correct'], sessionStorage[user_id]['image_id'] = get_obj(
                    geobjs,
                    sessionStorage[user_id]
                )
                if sessionStorage[user_id]['correct'] is not None:
                    res = display(res, sessionStorage[user_id])
                    return
                else:
                    res['response']['text'] = 'У меня закончились тесты :(, попробуйте сменить уровень сложности'
                    sessionStorage[user_id]['stage'] = 4
                    sessionStorage[user_id]['ingame'] = False
                    res['response']['buttons'] = [
                        {'title': 'Начать тест', 'hide': True},
                        {'title': 'Сменить уровень сложности', 'hide': True},
                        {'title': 'Показать свои результаты', 'hide': True}
                    ]
                    return

            else:
                res['response']['text'] = \
                    'Ответ неверный, попробуйте еще раз'

                res['response']['buttons'] = [
                    {'title': 'Пропустить', 'hide': True},
                    {'title': 'Показать еще раз', 'hide': True},
                ]

                if sessionStorage[user_id]['difficulty'] == 1:
                    res['response']['buttons'].append({'title': 'Сменить уровень сложности на Легко', 'hide': True})
                if sessionStorage[user_id]['difficulty'] == 2:
                    res['response']['buttons'].append({'title': 'Сменить уровень сложности на Средне', 'hide': True})

                return

    else:  # Если пользователь не в процессе тестирования

        res['response']['buttons'] = [
            {'title': 'Начать тест', 'hide': True},
            {'title': 'Сменить уровень сложности', 'hide': True},
            {'title': 'Показать свои результаты', 'hide': True}
        ]

        # Если пользователь хочет увидеть свои результаты
        if req['request']['original_utterance'].lower() in [
            'покажи результаты',
            'показать результаты',
            'результаты',
            'мои результаты',
            'статистика',
            'моя статистика',
            'показать свои результаты'
        ]:
            print('keko', get_stats(sessionStorage[user_id]))
            res['response']['text'] = get_stats(sessionStorage[user_id])
            return

        # Если пользователь хочет начать тест
        if req['request']['original_utterance'].lower() in [
            'начать',
            'начать тест',
            'старт',
        ]:
            try:
                # print(geobjs[sessionStorage[user_id]['difficulty']])
                # print(geobjs[sessionStorage[user_id]['difficulty']].keys())
                sessionStorage[user_id]['correct'], sessionStorage[user_id]['image_id'] = get_obj(
                    geobjs,
                    sessionStorage[user_id]
                )
                if sessionStorage[user_id]['correct'] is not None:
                    res = display(res, sessionStorage[user_id])
                    sessionStorage[user_id]['stage'] = 3
                    sessionStorage[user_id]['ticks'] += 1
                    sessionStorage[user_id]['ingame'] = True
                    return
                else:
                    res['response']['text'] = 'У меня закончились тесты :(, попроюуйте сменить уровень сложности'
                    sessionStorage[user_id]['stage'] = 4
                    sessionStorage[user_id]['ingame'] = False
                    return
                # res['response']['card']['type'] = 'BigImage'
                # res['response']['card']['image_id'] = geobjs[sessionStorage[user_id]['difficulty']][correct]

            except Exception as e:
                logging.error(str(e) + 'in start testing')
                traceback.print_exc()
                # res['response']['text'] = str(e)
                res['response']['text'] = 'Что-то пошло не так :('
            return

        # Если пользователь хочет сменить уровень сложности
        if req['request']['original_utterance'].lower().startswith('сменить уровень сложности'):
            try:  # Если в конце ответа пользователя явно указан уровень сложности
                sessionStorage[user_id]['difficulty'] = difs.index(
                    req['request']['original_utterance'].lower().split()[-1])
            except ValueError:  # Иначе перекидываем пользователя в меню выбора сложности
                res['response']['text'] = 'Доступно: легко, средне и сложно'
                sessionStorage[user_id]['stage'] = 1
                res['response']['buttons'] = [
                    {'title': 'Легко', 'hide': True},
                    {'title': 'Средне', 'hide': True},
                    {'title': 'Сложно', 'hide': True}
                ]
                return
            res['response']['text'] = 'Вы успешно сменили уровень сложности на {}'.format(
                difs[sessionStorage[user_id]['difficulty']]
            )
            sessionStorage[user_id]['stage'] = 4
            return

        # Если польхователь не ввел команду
        res['response']['text'] = 'Не могу распознать команду'
        return


# Получение результатов пользователя
def get_stats(userStorage):
    if userStorage['ticks'] == 0:
        perc = '0.0'
    else:
        perc = str(round(userStorage['good_ans'] * 100 / userStorage['ticks'], 3))
    return '''Ваши результаты:
    Всего вопросов: {}
    Правильных ответов: {}
    Процент выполнения: {}%'''.format(str(userStorage['ticks']), str(userStorage['good_ans']), perc)


'''# Формирования вопроса теста
def show(userStorage, res):
    correct, image_id = get_obj(userStorage['difficulty'], userStorage)
    res = display(res, image_id)
    return res'''


# Показ спутникового снимка
def display(res, userStorage):
    res['response']['buttons'] = [
        {'title': 'Пропустить', 'hide': True},
        {'title': 'Показать еще раз', 'hide': True},
        {'title': 'Пауза', 'hide': True}
    ]
    res['response']['text'] = \
        'Тут должна быть картинка'
    res['response']['card'] = {
        'type': 'BigImage',
        'image_id': userStorage['image_id'],
        'title': 'Вопрос №{} \n Введите название города'.format(userStorage['ticks'] + 1)
    }
    return res


# Формирование новой картинки теста
def get_obj(obj_list, userStorage):
    all = set(geobjs[userStorage['difficulty']].keys())
    shown = set(userStorage['shown'])
    try:
        corr = choice(list(all.difference(shown)))
    except:
        return None, None
    userStorage['shown'].append(corr)
    image_id = geobjs[userStorage['difficulty']][corr]
    return corr, image_id


if __name__ == '__main__':
    app.run()

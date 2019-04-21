import json
import requests
from random import shuffle


f_easy = open('Samples/objects_easy.txt', mode='r')
f_medium = open('Samples/objects_medium.txt', mode='r')
f_hard = open('Samples/objects_hard.txt', mode='r')

easy_list = list(map(lambda x: x[:-1], f_easy.readlines()))
medium_list = list(map(lambda x: x[:-1], f_medium.readlines()))
hard_list = list(map(lambda x: x[:-1], f_hard.readlines()))

objs = [
    easy_list,
    medium_list,
    hard_list
]

dat = [
    {},
    {},
    {}
]

search_api_server = "https://search-maps.yandex.ru/v1/"
map_api_server = "http://static-maps.yandex.ru/1.x/"
api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"
search_params = {
    "apikey": api_key,
    "lang": "ru_RU",
    "type": "geo",
    "text": ""
}
map_params = {
    "ll": None,
    "spn": None,
    "l": None,
    "pt": None
}

iden = 'fdbeb9a3-d8ae-4bc2-9e35-0f9d03a02980'  # Для яндекс диалогов
url = 'https://dialogs.yandex.net/api/v1/skills/{}/images'.format(iden)
par = {
    "Authorization": "OAuth AQAAAAAeLNe2AAT7o6vETdN1b0Lpr36lKkMn0Xk",
    "Content-Type": "application/json"
}

for i in range(3):
    for obj in objs[i]:
        search_params["text"] = obj
        response = requests.get(search_api_server, params=search_params)
        json_response = response.json()

        city_object = json_response["features"][0]

        point = city_object["geometry"]["coordinates"]

        spn1 = city_object["properties"]["boundedBy"][0][0] - city_object["properties"]["boundedBy"][1][0]
        spn2 = city_object["properties"]["boundedBy"][0][1] - city_object["properties"]["boundedBy"][1][1]

        spn = abs(max(spn1, spn2))

        map_params["ll"] = "{},{}".format(point[0], point[1])
        map_params["l"] = 'sat'
        map_params["spn"] = "{},{}".format(spn, spn)
        map_params["pt"] = "{},{},comma".format(point[0], point[1])
        map_response = requests.get(map_api_server, params=map_params)

        r = requests.post(url, data=json.dumps({"url": map_response.url}), headers=par)

        print(r.json()['image']['id'])
        dat[i][obj] = r.json()['image']['id']

js = open('Samples/geobjs.json', mode='w')
json.dump(dat, js)

print(dat)

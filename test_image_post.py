import requests
import json

iden = 'fdbeb9a3-d8ae-4bc2-9e35-0f9d03a02980'
map_url = "https://static-maps.yandex.ru/1.x/?ll=37.620070,55.753630&size=450,450&z=13&l=map&pt=37.620070,55.753630,pmwtm1~37.64,55.76363,pmwtm99"
url = 'https://dialogs.yandex.net/api/v1/skills/{}/images'.format(iden)
par = {
    "Authorization": "OAuth AQAAAAAeLNe2AAT7o6vETdN1b0Lpr36lKkMn0Xk",
    "Content-Type": "application/json"
}
r = requests.post(url, data=json.dumps({"url": map_url}), headers=par)
print(r.url)
print(r.json())

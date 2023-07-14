import requests
from pprint import pprint as pp
import os
from dotenv import load_dotenv
import json

load_dotenv()

access_token = os.getenv('ACCESS_TOKEN')

url =  f'https://api.vk.com/method/groups.get?v=5.124&extended=1&access_token={access_token}'
response = requests.get(url)

with open('API/groups_get.json', 'w', encoding='utf-8') as file:
    data = response.json()['response']['items']
    for dictionary in data:
        keys_to_remove_is = [key for key in dictionary.keys() if key.startswith('is')]
        for key in keys_to_remove_is:
            dictionary.pop(key)
    json.dump(data, file, ensure_ascii=False, indent=4)


import requests
import json


link = 'https://api.github.com/users/StanleyIG/repos'
r = requests.get(link)
data = r.json()

with open('API/github_repos.json', 'w', encoding='utf-8') as file:
    to_json = [{'owner': dictionary['owner']['login'],
                'repository':dictionary['name']} for dictionary in data]
    json.dump(to_json, file, ensure_ascii=False, indent=4)
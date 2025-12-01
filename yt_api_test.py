import requests

BASE_URL = "https://youtrack.ispsystem.net/"
TOKEN = "perm-YS5taWxpbmV2c2tpaQ==.NTgtOTQ=.1RhOjxGFM1XV4qEVRb8WwShbIjfN36"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json"
}

resp = requests.get(f"{BASE_URL}/api/users/me?fields=login,fullName", headers=headers)
print(resp.json())



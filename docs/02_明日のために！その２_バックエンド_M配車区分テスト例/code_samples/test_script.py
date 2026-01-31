import requests

BASE_URL = "http://localhost:8091"

login_res = requests.post(
    f"{BASE_URL}/core/auth/ログイン",
    json={"利用者ID": "admin", "パスワード": "********"},
    timeout=10
)
login_res.raise_for_status()
TOKEN = login_res.json()["data"]["access_token"]
headers = {"Authorization": f"Bearer {TOKEN}"}

payload = {
    "配車区分ID": "99",
    "配車区分名": "検証",
    "配車区分備考": "青",
    "配色枠": "#001f3f",
    "配色背景": "#cce6ff",
    "配色前景": "#000000"
}

create_res = requests.post(
    f"{BASE_URL}/apps/M配車区分/登録",
    json=payload,
    headers=headers,
    timeout=10
)
print("create:", create_res.json()["status"])

get_res = requests.post(
    f"{BASE_URL}/apps/M配車区分/取得",
    json={"配車区分ID": "99"},
    headers=headers,
    timeout=10
)
print("get:", get_res.json()["status"])

payload.update({"配車区分備考": "赤", "配色枠": "#660000", "配色背景": "#ffcccc"})
update_res = requests.post(
    f"{BASE_URL}/apps/M配車区分/変更",
    json=payload,
    headers=headers,
    timeout=10
)
print("update:", update_res.json()["status"])

list_res = requests.post(
    f"{BASE_URL}/apps/M配車区分/一覧",
    json={},
    headers=headers,
    timeout=10
)
print("list:", list_res.json()["status"], "total:", list_res.json()["data"]["total"])

delete_res = requests.post(
    f"{BASE_URL}/apps/M配車区分/削除",
    json={"配車区分ID": "99"},
    headers=headers,
    timeout=10
)
print("delete:", delete_res.json()["status"])


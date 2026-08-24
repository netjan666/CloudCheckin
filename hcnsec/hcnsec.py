"""hcnsec 多账户每日签到"""
import os
import time
import random
from dotenv import load_dotenv
from curl_cffi import requests
from telegram.notify import send_source_notification

load_dotenv()

BASE_URL = "https://api.hcnsec.cn"

# 从环境变量读取多账户 (用 & 分隔)
usernames = os.environ.get("HCN_SEC_USERNAME", "").strip()
passwords = os.environ.get("HCN_SEC_PASSWORD", "").strip()
user_ids = os.environ.get("HCN_SEC_USER_ID", "").strip()

def main():
    results = []
    failed = False

    if not usernames:
        results.append("Config error: HCN_SEC_USERNAME not set")
        send_source_notification("HCN_SEC", results)
        return 1

    username_list = usernames.split("&")
    password_list = passwords.split("&")
    user_id_list = user_ids.split("&")

    if len(username_list) != len(password_list) or len(username_list) != len(user_id_list):
        results.append(f"Config error: account count mismatch (usernames={len(username_list)}, passwords={len(password_list)}, ids={len(user_id_list)})")
        send_source_notification("HCN_SEC", results)
        return 1

    for i, (username, password, user_id) in enumerate(zip(username_list, password_list, user_id_list)):
        account = i + 1
        username = username.strip()
        password = password.strip()
        user_id = user_id.strip()

        print(f"[Account {account}] {username}...", flush=True)

        # 随机延迟
        if i > 0:
            delay = random.randint(1, 10)
            time.sleep(delay)

        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})

        try:
            # 登录
            r = session.post(f"{BASE_URL}/api/user/login", json={
                "username": username,
                "password": password
            }, timeout=15, impersonate="chrome136")

            if r.status_code != 200 or not r.json().get("success", True):
                result = f"Account {account} ({username}): login failed — {r.status_code}"
                failed = True
                results.append(result)
                print(result, flush=True)
                continue

            login_user = r.json()["data"].get("username", "?")
            print(f"  Login OK: {login_user}", flush=True)

            # 签到
            r2 = session.post(f"{BASE_URL}/api/user/checkin",
                              headers={"New-Api-User": user_id},
                              timeout=15, impersonate="chrome136")

            checkin = r2.json()
            if r2.status_code == 200 and checkin.get("success"):
                quota = checkin.get("data", {}).get("quota_awarded", "?")
                result = f"Account {account} ({username}): check-in successful (+{quota})"
            else:
                msg = checkin.get("message", "unknown")
                result = f"Account {account} ({username}): {msg}"
                if "失败" in msg or "错误" in msg:
                    failed = True

            print(f"  {result}", flush=True)
            results.append(result)

        except Exception as e:
            result = f"Account {account} ({username}): error — {e}"
            failed = True
            results.append(result)
            print(f"  {result}", flush=True)

    send_source_notification("HCN_SEC", results)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

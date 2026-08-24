"""hcnsec 多账户每日签到（支持用户名/密码 + 令牌两种方式）"""
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
tokens = os.environ.get("HCN_SEC_TOKEN", "").strip()  # 可选，令牌签到


def main():
    results = []
    failed = False

    username_list = [u.strip() for u in usernames.split("&") if u.strip()]
    password_list = [p.strip() for p in passwords.split("&") if p.strip()]
    user_id_list = [i.strip() for i in user_ids.split("&") if i.strip()]
    token_list = [t.strip() for t in tokens.split("&") if t.strip()] if tokens else []

    if not username_list:
        results.append("Config error: HCN_SEC_USERNAME not set")
        send_source_notification("HCN_SEC", results)
        return 1

    if len(username_list) != len(user_id_list):
        results.append(f"Config error: account count mismatch")
        send_source_notification("HCN_SEC", results)
        return 1

    total = len(username_list)

    for i, (username, user_id) in enumerate(zip(username_list, user_id_list)):
        account = i + 1
        print(f"[Account {account}/{total}] {username}...", flush=True)

        if i > 0:
            delay = random.randint(1, 10)
            time.sleep(delay)

        try:
            # 判断是否有令牌
            token = token_list[i] if i < len(token_list) and token_list[i] else ""
            password = password_list[i] if i < len(password_list) else ""

            if token:
                # 令牌签到：直接调用 checkin，不需要 login
                print(f"  Using token auth", flush=True)
                r = requests.post(
                    f"{BASE_URL}/api/user/checkin",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {token}",
                        "New-Api-User": user_id,
                    },
                    timeout=15,
                    impersonate="chrome136",
                )
            else:
                # 用户名/密码签到：先 login 再 checkin
                session = requests.Session()
                session.headers.update({"Content-Type": "application/json"})

                r_login = session.post(
                    f"{BASE_URL}/api/user/login",
                    json={"username": username, "password": password},
                    timeout=15,
                    impersonate="chrome136",
                )

                if r_login.status_code != 200 or not r_login.json().get("success", True):
                    result = f"Account {account} ({username}): login failed — {r_login.status_code}"
                    failed = True
                    results.append(result)
                    print(f"  {result}", flush=True)
                    continue

                login_user = r_login.json()["data"].get("username", "?")
                print(f"  Login OK: {login_user}", flush=True)

                r = session.post(
                    f"{BASE_URL}/api/user/checkin",
                    headers={"New-Api-User": user_id},
                    timeout=15,
                    impersonate="chrome136",
                )

            checkin = r.json()
            if r.status_code == 200 and checkin.get("success"):
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

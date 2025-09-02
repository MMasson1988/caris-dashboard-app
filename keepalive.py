# keepalive.py
# -*- coding: utf-8 -*-
import os, time, random, sys
import requests

APP_URL = os.getenv("SHINYAPP_URL", "https://massonmoise.shinyapps.io/dashboard-pvvih/")  # <-- remplace
TIMEOUT = int(os.getenv("TIMEOUT", "25"))
RETRIES = int(os.getenv("RETRIES", "5"))
BACKOFF = float(os.getenv("BACKOFF", "2.0"))

def ping(url):
    # param aléatoire pour éviter caches intermédiaires
    url = url.rstrip("/") + f"/?_keepalive={random.randint(100000,999999)}"
    for i in range(1, RETRIES + 1):
        try:
            r = requests.get(url, timeout=TIMEOUT, allow_redirects=True)
            # 200/302/303/307/308 = OK pour “réveiller”
            if r.status_code in (200, 302, 303, 307, 308):
                print(f"[OK] {r.status_code} {r.url}")
                return True
            else:
                print(f"[WARN] HTTP {r.status_code} essai {i}/{RETRIES}")
        except requests.RequestException as e:
            print(f"[ERR] {e} essai {i}/{RETRIES}")
        time.sleep(BACKOFF * i)  # backoff progressif
    return False

if __name__ == "__main__":
    ok = ping(APP_URL)
    sys.exit(0 if ok else 1)

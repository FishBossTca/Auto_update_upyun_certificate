#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import requests
from time import sleep

# ========= 配置信息 =========
- USERNAME = "你的账户"
- PASSWORD = "你的密码"
- DOMAIN   = "证书域名"
- KEY_PATH = "密钥路经"
- CERT_PATH= "证书路经"
# ===========================

URL = {
    "login":   "https://console.upyun.com/accounts/signin/",
    "list":    "https://console.upyun.com/api/https/certificate/list/?limit=50",
    "upload":  "https://console.upyun.com/api/https/certificate/",
    "migrate": "https://console.upyun.com/api/https/migrate/certificate",
    "delete":  "https://console.upyun.com/api/https/certificate/?certificate_id={}"
}

session = requests.Session()

def error(msg): print(f"✘ {msg}"); sys.exit(1)
def info(msg):  print(f"➤ {msg}")
def ok(msg):    print(f"✔ {msg}")

def login():
    info("登录中...")
    r = session.post(URL["login"], json={"username": USERNAME, "password": PASSWORD})
    if r.status_code != 200 or not session.cookies.get("s"):
        error("登录失败，请检查用户名密码")
    ok("登录成功")

def get_cert_id():
    r = session.get(URL["list"])
    certs = r.json().get("data", {}).get("result", {})
    for cid, c in certs.items():
        if c.get("commonName") == DOMAIN:
            ok(f"旧证书 ID: {cid}")
            return cid
    error(f"找不到域名 {DOMAIN} 的证书")

def upload_cert():
    info("上传新证书...")
    try:
        cert = open(CERT_PATH).read().strip()
        key  = open(KEY_PATH).read().strip()
    except Exception as e:
        error(f"读取证书失败：{e}")
    r = session.post(URL["upload"], json={"certificate": cert, "private_key": key})
    if r.status_code == 200:
        cid = r.json()["data"]["result"]["certificate_id"]
        ok(f"上传成功，新证书 ID: {cid}")
        return cid
    error("上传失败")

def migrate_cert(old_id, new_id):
    info("迁移证书...")
    r = session.post(URL["migrate"], json={"old_crt_id": old_id, "new_crt_id": new_id})
    if r.status_code == 200 and r.json().get("data", {}).get("result"):
        ok("迁移成功")
    else:
        error("迁移失败")

def delete_cert(cert_id):
    info("等待 5 秒后删除旧证书...")
    sleep(5)
    r = session.delete(URL["delete"].format(cert_id))
    try: data = r.json().get("data", {})
    except: error("删除失败：返回内容不是 JSON")

    if r.status_code == 200 and data.get("status"):
        ok("旧证书删除成功")
    elif data.get("type") == "ThereIsBindingDomains":
        print("⚠️ 旧证书仍绑定域名，无法删除")
    else:
        error(f"删除失败：{r.text}")

def main():
    login()
    old_id = get_cert_id()
    new_id = upload_cert()

    if new_id == old_id:
        print("⚠️ 新旧证书 ID 相同，跳过迁移与删除")
        return

    sleep(3)  # 等待新证书生效
    migrate_cert(old_id, new_id)
    delete_cert(old_id)

if __name__ == "__main__":
    main()

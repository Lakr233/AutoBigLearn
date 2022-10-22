import os
import requests
import re
from errno import EPERM

# get open id from env OPEN_ID
config_openid = os.environ.get('OPEN_ID')

assert config_openid, 'OPEN_ID is not set'

base_endpoint = "https://qczj.h5yunban.com/qczj-youth-learning/"

print("[*] starting script with openid %s" % config_openid)

# ===============================================================================
print("[*] requesting access token...")
access_token = ""
try:
    url = base_endpoint + "cgi-bin/login/we-chat/callback"
    parms = {
        "callback": base_endpoint + "qczj-youth-learning/index.php",
        "appid": "wx56b888a1409a2920",
        "openid": config_openid,
    }
    # URL GET
    resp = requests.get(url, params=parms)
    resp_text = resp.text

    # extract access token which formats as UUID
    regex_uuid = "[A-Z0-9]{8}[-][A-Z0-9]{4}[-][A-Z0-9]{4}[-][A-Z0-9]{4}[-][A-Z0-9]{12}"
    access_token = re.findall(regex_uuid, resp_text)[0]
except Exception as e:
    print("[E] failed to acquire access token: %s" % e)
    exit(EPERM)
print("[*] acquired access token: %s" % access_token)


# ===============================================================================
print("[*] requesting user info...")
user_details = {}
organization_id = ""
try:
    url = base_endpoint + "cgi-bin/user-api/course/last-info"
    parms = {
        "accessToken": access_token
    }
    resp = requests.get(url, params=parms)
    user_details = resp.json()["result"]
except Exception as e:
    print("[E] failed to acquire user info: %s" % e)
    exit(EPERM)
try:
    print("[*] script is now working for: %s" % user_details["cardNo"])
    for nodes in user_details["nodes"]:
        try:
            oid = nodes["id"]
            print("[*] found organization node with name: %s" % nodes["title"])
            if len(oid) > len(organization_id):
                print("[*] updating longer organization id to %s" % oid)
                organization_id = oid
        except:
            continue
    print("[*] script now working for organization: %s" % organization_id)
except Exception as e:
    print("[E] failed to acquire user info: %s" % e)
    exit(EPERM)


# ===============================================================================
print("[*] requesting current course...")
course_details = {}
try:
    url = base_endpoint + "cgi-bin/common-api/course/current"
    parms = {
        "accessToken": access_token
    }
    resp = requests.get(url, params=parms)
    resp_json = resp.json()
    course_details = resp_json["result"]
except Exception as e:
    print("[E] failed to acquire current course: %s" % e)
    exit(EPERM)
try:
    print("[*] current course type: %s" % course_details["type"])
    print("[*] current course id: %s" % course_details["id"])
    print("[*] current course title: %s" % course_details["title"])
    print("[*] current course uri: %s" % course_details["uri"])
except Exception as e:
    print("[E] failed to acquire current course details: %s" % e)
    exit(EPERM)


# ===============================================================================
print("[*] begin check in...")
try:
    url = base_endpoint + "cgi-bin/user-api/course/join"
    parms = {
        "accessToken": access_token
    }
    body = {
        "nid": organization_id,
        "course": course_details["id"],
        "cardNo": user_details["cardNo"]
    }
    # POST
    resp = requests.post(url, params=parms, json=body)
    resp_json = resp.json()
    # assert status = 200
    assert resp_json["status"] == 200
    print("[*] check in return id: %s" % resp_json["result"]["id"])
    print("[*] check in return ip: %s" % resp_json["result"]["userIp"])
except Exception as e:
    print("[E] failed to check in: %s" % e)
    exit(EPERM)

print("[*] done check in!")

if os.environ.get("BARK_ENDPOINT") is not None:
    bark_endpoint = os.environ.get("BARK_ENDPOINT")
    bark_message = "学生%s已完成%s%s的签到。" % (
        user_details["cardNo"],
        course_details["type"],
        course_details["title"],
    )
    bark_group = "自动大学习"
    bark_request = bark_endpoint + "%s/%s?group=%s" % (
        bark_group,
        bark_message,
        bark_group,
    )
    requests.get(bark_request)

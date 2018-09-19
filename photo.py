# -*- coding:utf-8 -*-
import requests
import json
import re
import shutil
import time
from datetime import datetime, timedelta, timezone
import urllib.request, urllib.error
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# SLACK =================
#slackのAPI/channel/ファイルの一覧を取得する
slack_API_token = "取得したAPI TOKEN KEY"
channel = "チャンネルID"
# SLACK =================

# HEADERS =================
# スクレイピング・クローリングする時のマナー的な
headers = {"User-Agent": "browsers:ブラウザ名, OS:OS名"}
# HEADERS =================

# GOOGLE =================
# Google認証を行う
gauth = GoogleAuth()
gauth.CommandLineAuth(GoogleAuth())

# Google Driveのオブジェクトを得る --- (*1)
drive = GoogleDrive(gauth)

# Drive内のフォルダID
folder_id = "アップロード先となるGoogle Drive内のフォルダID"
# GOOGLE =================

# 各処理の関数 =================
def download_imgurl(url, file_name):
    res = requests.get(url, stream=True)
    if res.status_code == 200:
        with open(file_name, 'wb') as file:
            shutil.copyfileobj(res.raw, file)
        return 1
    else:
        return -1

def make_list(files_list_name):
    id_list = []
    for i in img_files:
        if i['files'] != "":
            id_list.append(i['files'][0]['id'])
    return id_list

def make_timedate(int_days_ago):    #int_days_agoはint型で負の数 例）-1=>前日 -2=>一昨日
    now = datetime.now()
    yesterday = now + timedelta(days=int_days_ago)
    yesterday = yesterday.strftime('%s')
    return yesterday

def get_img_url(slack_API_token, id_number):
    # 1) API files.sharedPublicURLを使う
    public_url = "https://slack.com/api/files.sharedPublicURL?token=%s&file=%s&pretty=1" % (slack_API_token, id_number)
    # 2) files.sharedPublicURLをutf-8に変換しstrで利用できる状態にする
    response_share = urllib.request.urlopen(public_url).read().decode("utf-8")
    # 3) permalink_publicを検索し公開用URLの取得を可能にする正規表現をコンパイルする。
    pubhtml_pattern = re.compile(r'\"permalink_public\": \"([a-zA-Z0-9!-/:-@¥[-`{-~]+)\",\n')
    # 4) pubhtml_patternを使い、公開用URLを取得。さらにその中に含まれるバックスラッシュ「\」を取り除く。
    img_html_url  = pubhtml_pattern.findall(response_share)[0].replace("\\","")
    # 5) 公開用URLにアクセスしソースを取得。strに変換する。
    response_get_img = urllib.request.urlopen(img_html_url).read().decode("utf-8")
    # 6) 画像取得するための正規表現をコンパイルする。
    puburl_pattern = re.compile(r'<img src=\"([a-zA-Z0-9!-/:-@¥[-`{-~]+)\">\n')
    # 7) 画像を表すタグimg src=~を取得する
    img_url  = puburl_pattern.findall(response_get_img)[0]
    # 8) 取得した画像のURLを返す
    return img_url
# 各処理の関数 =================

# 前日のタイムスタンプを取得
yesterday = make_timedate(-1)

# 画像のID取得
file_list_url = "https://slack.com/api/channels.history?token=%s&channel=%s&oldest=%s&pretty=1" % (slack_API_token, channel, yesterday)
response1  = requests.get(file_list_url, headers=headers)
json_data = response1.json()
img_files = json_data['messages']
id_list = make_list(img_files)

# slackからのダウンロード処理
try:
    print('I will download...')
    for num in id_list:
        img_url = get_img_url(slack_API_token, num)
        download_imgurl(img_url, num + '.jpg')
    print('Complete!!')
except:
    print("ERROR: ", num + "download failed...")
    pass

print('Disable the URL...')
for ber in id_list:
    revoke_url = "https://slack.com/api/files.revokePublicURL?token=%s&file=%s&pretty=1" % (slack_API_token, ber)
    response_revo = urllib.request.urlopen(revoke_url).read()
print('Complete!!')

# Driveへのアップロード処理
for j in id_list:
    img_name = j + '.jpg'
    f = drive.CreateFile({
        'title': img_name,
        'mimeType': 'image/jpeg',
        'parents': [{'kind': 'drive#fileLink', 'id':folder_id}]
        })
    f.SetContentFile(img_name)
    f.Upload()
print("Upload Complte!!")

# up 头像
# https://i0.hdslb.com/bfs/face/
# 视频封面
# https://i2.hdslb.com/bfs/archive/

import requests
import time
import threading
import random
import os.path

import pandas as pd
import datetime

img_link_body_list = [
                    'https://i0.hdslb.com/bfs/archive/{}', # pic
                    'https://i0.hdslb.com/bfs/face/{}' # face
                    ]

total_num = 0
remaining_num = 0

thread_num_max = 4
semlock = threading.BoundedSemaphore(thread_num_max)

def getImage(img_link, img_name, retry_count=0):
    global remaining_num, total_num
    if os.path.exists(img_name):
        print(f'+++ Existed: {img_name}')
        remaining_num -= 1
        print(f'=== Remaining: {remaining_num:{0}{3}}/{total_num:{0}{3}} ===')
        return

    try:
        print(f'>>> Getting image: {img_link}')
        img = requests.get(img_link)
    except Exception as exc:
        retry_count += 1
        if retry_count >= 5:
            print(f'--- Exceeded retry limits: {img_name}')
            return
        else:
            print(f'*** Retry {retry_count} times to get: {img_name} ...')
            getImage(img_link, img_name, retry_count)
    else:
        with open(img_name, 'wb') as img_file:
            img_file.write(img.content)
        print(f'+++ Successfully dumped: {img_name}')
        remaining_num -= 1
        print(f'=== Remaining: {remaining_num:{0}{3}}/{total_num:{0}{3}} ===')

    semlock.release()

def createThread(img_link, img_ext, xid, xtype):
    semlock.acquire()

    xid_name = ('mid', 'aid')[xtype=='pic']
    # xid_name = ('aid', 'mid')[xtype=='face']

    img_name = f'{xtype}/{xid_name}_{xid}{img_ext}'
    thrd = threading.Thread(target=getImage, args=[img_link, img_name])

    return thrd

def startThread(thrd):
    # thrd.daemon = True
    thrd.start()
def joinThread(thrd):
    thrd.join()

pic_list = []
face_list = []
aid_list = []
mid_list = []
df = pd.read_csv('./data/view_gt100w_180731.CSV', sep=',')

def getInfoList():
    global pic_list, face_list
    global total_num, remaining_num

    total_num = len(df) * 2
    remaining_num = total_num

    for i in range(len(df)):
        pic_list.append(df['pic'][i])
        face_list.append(df['face'][i])
        aid_list.append(df['aid'][i])
        mid_list.append(df['mid'][i])

def getAllImages():
    pic_thrd_pool = []
    face_thrd_pool = []

    pic_img_link_body = img_link_body_list[0]
    face_img_link_body = img_link_body_list[1]

    for i in range(10):
        # pic_test = '1c1480299d2105c1bd0db584eec8932ebf0c8097.jpg' # pic: aid_17515643
        # face_test = '163812458cbd1b2fc04e7c02c8075700867fcbb7.jpg' # face: mid_10769575
        pic_tmp = pic_list[i]
        face_tmp = face_list[i]
        aid_tmp = aid_list[i]
        mid_tmp = mid_list[i]

        pic_img_link = pic_img_link_body.format(pic_tmp)
        pic_img_ext = os.path.splitext(pic_tmp)[1]

        pic_thrd = createThread(pic_img_link, pic_img_ext, xid=aid_tmp, xtype='pic')
        pic_thrd_pool.append(pic_thrd)

        face_img_link = face_img_link_body.format(face_tmp)
        face_img_ext = os.path.splitext(face_tmp)[1]

        face_thrd = createThread(face_img_link, face_img_ext, xid=mid_tmp, xtype='face')
        face_thrd_pool.append(face_thrd)

    for pic_thrd in pic_thrd_pool:
        startThread(pic_thrd)
    for pic_thrd in pic_thrd_pool:
        startThread(pic_thrd)
    for pic_thrd in pic_thrd_pool:
        joinThread(pic_thrd)
    for face_thrd in face_thrd_pool:
        joinThread(face_thrd)

if __name__ == '__main__':
    getInfoList()
    getAllImages()
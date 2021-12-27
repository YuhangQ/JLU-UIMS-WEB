import io
import json
import os
import uuid
import re
import sys
from hashlib import md5

import requests
from PIL import Image

s = requests.session()

username = sys.argv[1]
password = sys.argv[2]

headers = {'Content-Type': 'application/json'}

print('\n\n正在登录...')

j_password = md5(('UIMS' + username + password).encode()).hexdigest()

a = s.get("https://uims.jlu.edu.cn/ntms/open/get-captcha-image.do?s=1").content
byte_stream = io.BytesIO(a)

im = Image.open(byte_stream)

imPath = os.path.abspath(__file__) + str(uuid.uuid1()) + ".png"
im.save(imPath)

import ddddocr
ocr = ddddocr.DdddOcr()
res = ocr.classification(byte_stream.getbuffer())
print("OCR自动识别验证码:" + res)

try:
    vcode = res
    cookies = {
        'loginPage': 'userLogin.jsp',
        'alu': username
    }
    requests.utils.add_dict_to_cookiejar(s.cookies, cookies)

    post_data = {
        'username': username,
        'password': j_password,
        'mousePath': '',
        'vcode': vcode
    }
    r = s.post('http://uims.jlu.edu.cn/ntms/j_spring_security_check', data=post_data)

    message = re.findall('<span class="error_message" id="error_message">(.*?)</span>', r.text)
    
    r = s.post('http://uims.jlu.edu.cn/ntms/action/getCurrentUserInfo.do')
    info = json.loads(r.text)
    name = info['loginInfo']['nickName']
    t = info['groupsInfo'][0]['groupName']
except Exception as e:
    if message:
        print(message[0])
    print("验证码是AI识别，也可能会有错误，请刷新页面重新试试。")
    exit(0)

if info['userType'] == 'S' or t == '学生':
    t = '同学'

if t == '同学':
    print("登录成功！欢迎您：" + name + " " + t + '！\n')
else:
    print("您好，" + name + ' ' + t + '！系统检测到您可能不是学生，无法进行教学质量评价，感谢您的支持！\n')

post_url = 'http://uims.jlu.edu.cn/ntms/service/res.do'

defRes = info['defRes']
schId = defRes['school']
deptId = defRes['department']
adcId = defRes['adcId']

classmate_list = []
post_data = {
    "tag": "student_sch_dept",
    "branch": "default",
    "params": {"schId": "%s" % schId,
               "deptId": "%s" % deptId,
               "adcId": "%s" % adcId}
}
r = s.post(post_url, data=json.dumps(post_data), headers=headers)
classmate_info = json.loads(r.text)['value']
for classmate in classmate_info:
    classmate_list.append(classmate['name'])

print('正在查询可评课程...')
post_data = {
    "tag": "student@evalItem",
    "branch": "self",
    "params": {"blank": "Y"}
}

r = s.post('http://uims.jlu.edu.cn/ntms/service/res.do', data=json.dumps(post_data), headers=headers)
eval_info = json.loads(r.text)['value']
num = len(eval_info)
if num == 0:
    post_data = {
        "tag": "student@evalItem",
        "branch": "self",
        "params": {"done": "Y"}
    }
    r = s.post('http://uims.jlu.edu.cn/ntms/service/res.do', data=json.dumps(post_data), headers=headers)
    finish_info = json.loads(r.text)['value']
    if len(finish_info) == 0:
        print('当前可能并非教学质量评价时段，没有可评价的课程！\n')
        print('感谢您的使用！\n')
        exit()
    else:
        print('您已完成所有 %d 条评价项，无需进行评教！\n' % len(finish_info))
        print('感谢您的使用！\n')
        exit()
else:
    print('您还有 %d 条未完成的评价\n' % num)

print('正在进行教学质量评价...\n')
count = 0
puzzle = ''
for course in eval_info:
    id = course['evalItemId']
    post_data = {"evalItemId": "%s" % id}
    post_url = 'https://uims.jlu.edu.cn/ntms/action/eval/fetch-eval-item.do'
    r = s.post(post_url, data=json.dumps(post_data), headers=headers)
    puzzle_info = json.loads(r.text)['items'][0]['puzzle']
    flag = False

    for classmate in classmate_list:
        length = len(puzzle_info) if len(puzzle_info) < len(classmate) else len(classmate)
        for i in range(length):
            if puzzle_info[i] == '_':
                puzzle = classmate[i]
                cl_name = puzzle_info.replace('_', puzzle)

        if cl_name == classmate:
            flag = True
            break

    # 一般情况下均可获取到班级同学信息，可去掉 #
    if not flag:
        puzzle = input('请输入在下划线处对应的一个汉字，以构成一个你们班级同学的名字（%s）：' % puzzle_info)
        classmate_list.append(puzzle_info.replace('_', puzzle))
    ###

    post_url = 'http://uims.jlu.edu.cn/ntms/action/eval/eval-with-answer.do'
    post_data = {"guidelineId": 160, "evalItemId": "%s" % id,
                 "answers": {"p01": "A", "p02": "A", "p03": "A", "p04": "A",
                             "p05": "A", "p06": "A", "p07": "A", "p08": "A", "p09": "A",
                             "p10": "A", "sat11": "A", "sat12": "A", "sat13": "A", "puzzle_answer": "%s" % puzzle},
                 "clicks": {"_boot_": 0, "p01": 49050, "p02": 50509,
                            "p03": 52769, "p04": 54833, "p05": 58783,
                            "p06": 61488, "p07": 62599,
                            "p08": 64182, "p09": 68422, "p10": 70505,
                            "sat11": 71589, "sat12": 73270, "sat13": 185638}}
    s.post(post_url, data=json.dumps(post_data), headers=headers)
    count += 1
    print(str(count) + ' - ' + course['target']['name'] + ' 老师的 ' + course['targetClar']['notes'][2:] + ' 评价完成！\n')


print('教学质量评价已完成！')
print('\n\n感谢您的使用！\n\n')
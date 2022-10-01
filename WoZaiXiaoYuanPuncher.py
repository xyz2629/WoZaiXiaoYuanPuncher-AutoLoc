# -*- encoding:utf-8 -*-
import datetime
import requests
import json
import time
import hashlib
import random
sign_time = int(round(time.time() * 1000)) #13位
from urllib.parse import urlencode
from utils.dingdingBotUtil import DingDingBot

SchoolLocation = self.data['SchoolLocation']
#"陕西省西安市未央区西安工业大学"
key = self.data['key']
#"17c0b0909190e8fb031f927441f2ea35"
randomswitch = self.data['randomswitch']

class Getinfo:
    # 高德地图 搜索接口地址
    url = "https://restapi.amap.com/v3/geocode/geo?address=" + SchoolLocation + "&key=" + key
    # 取得结果
    res = requests.get(url)
    res = eval(res.text)
    # 取得的结果内geocodes为接下来所需结果
    res = res['geocodes']
    # 将list值转化为普通值
    res = res[0]
    # 经纬度
    def location(res):
        location=res['location']
        return location
    locloc = res['location']
    # 利用经纬度获取详细地址信息和towncode（主要是towncode）
    url1 = "https://restapi.amap.com/v3/geocode/regeo?location=" + locloc + "&key=" + key
    res1 = requests.get(url1)
    res1 = eval(res1.text)
    res2 = res1['regeocode']
    # 取得地址详细信息
    def location_info(res2):
        location_info=res2['addressComponent']
        return location_info
    res3 = res2['addressComponent']
    # 取得街道信息
    def streetinfo(res3):
        streetinfo = res3['streetNumber']
        return streetinfo
    # 上方取得的citycode为县级代码，而我在校园使用的市级，取得“xx市”
    loc_city = res3['city']
    # 请求 该市位置信息
    url = "https://restapi.amap.com/v3/geocode/geo?address=" + loc_city + "&key=" + key
    res4 = requests.get(url)
    res4 = eval(res4.text)
    # 取得结果
    res4 = res4['geocodes']
    res4 = res4[0]
    # 结果作为city_code
    def city_code(res4):
        city_code = res4['adcode']
        return city_code

class WoZaiXiaoYuanPuncher:
    def __init__(self, item):
        # 账号数据
        self.data = item
        # 登陆接口
        self.loginUrl = "https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/username"
        # 请求头
        self.header = {
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36 MicroMessenger/7.0.9.501 NetType/WIFI MiniProgramEnv/Windows WindowsWechat",
            "Content-Type": "application/json;charset=UTF-8",
            "Content-Length": "2",
            "Host": "gw.wozaixiaoyuan.com",
            "Accept-Language": "en-us,en",
            "Accept": "application/json, text/plain, */*"
        }
        # 请求体（必须有）
        self.body = "{}"
        # 实例化session
        self.session = requests.session()
        self.status_code = -1

    # 登陆
    def login(self):
        url = self.loginUrl + "?username=" + str(self.data['username']) + "&password=" + str(self.data['password'])
        # 登陆
        response = self.session.post(url=url, data=self.body, headers=self.header)
        res = json.loads(response.text)
        if res["code"] == 0:
            print("登陆成功")
            jwsession = response.headers['JWSESSION']
            self.setJwsession(jwsession)
            return True
        else:
            print("登陆失败，请检查账号信息")
            self.status_code = 5
            return False

    # 设置JWSESSION
    def setJwsession(self, jwsession):
        self.header['JWSESSION'] = jwsession

    # 获取JWSESSION
    def getJwsession(self):
        return self.header['JWSESSION']

    # 测试登陆状态，若未登录或jwsession失效，请求返回code=-10
    def testLoginStatus(self):
        # 用任意需要鉴权的接口即可，这里随便选了一个
        url = "https://student.wozaixiaoyuan.com/heat/getTodayHeatList.json"
        self.header['Host'] = "student.wozaixiaoyuan.com"
        response = self.session.post(url=url, data=self.body, headers=self.header)
        res = json.loads(response.text)
        if res['code'] == 0:
            # 已登陆
            return 1
        elif res['code'] == -10:
            # 未登录或jwsession失效
            self.status_code = 4
            return 0
        else:
            # 其他错误，打卡中止
            self.status_code = 0
            return -1

    # 获取打卡列表，判断当前打卡时间段与打卡情况，符合条件则自动进行打卡
    def PunchIn(self):
        url = "https://student.wozaixiaoyuan.com/heat/getTodayHeatList.json"
        self.header['Host'] = "student.wozaixiaoyuan.com"
        response = self.session.post(url=url, data=self.body, headers=self.header)
        res = json.loads(response.text)
        # 遍历每个打卡时段（不同学校的打卡时段数量可能不一样）
        print(res) # test
        if res['code'] == 0:
            for i in res['data']:
                # 判断时段是否有效，一般情况下同一时刻只有一个有效时段
                if int(i['state']) == 1:
                    # 判断是否已经打卡
                    if int(i['type']) == 0:
                        self.doPunchIn(str(i['seq']))
                    elif int(i['type']) == 1:
                        print("已经打过卡了")
        elif res['code'] == -10:
            print("未登录或jwsession过期")
            self.status_code = 4
        else:
            print("未知错误")
            self.status_code = 0

    # 执行打卡
    # 参数seq ： 当前打卡的序号
    def doPunchIn(self, seq):
        self.header['Host'] = "student.wozaixiaoyuan.com"
        self.header['Content-Type'] = "application/x-www-form-urlencoded"
        url = "https://student.wozaixiaoyuan.com/heat/save.json"

        # 将高德地图所有结果导入
        location = Getinfo.location(Getinfo.res)
        location_info = Getinfo.location_info(Getinfo.res2)
        streetinfo = Getinfo.streetinfo(Getinfo.res3)
        city_code = Getinfo.city_code(Getinfo.res4)
        coordinate = location.split(",")

        # 经纬度6位数后面填充随机数，对定位结果影响不大，但更接近我在校园真实经纬度获取
        if randomswitch == 1:
            random_a = random.randint(0, 9999999)
            random_a = str(random_a)
            random_b = random.randint(0, 9999999)
            random_b = str(random_b)
        else:
            random_a = ""
            random_b = ""

        # 导入towncode
        towncode = location_info['towncode']
        towncode = towncode[:-3]

        # 我在校园乡村打卡无此street结果，仅精确到镇，所以如此处理：如果检测到高德地图未返回street结果，则将list元素为空时的‘[]’去掉，保证结果正常
        if len(streetinfo['street']) == 0:
            streetinfo['street'] = ""

        # signature生成
        content = f"{location_info['province']}_{sign_time}_{location_info['city']}"
        signature = hashlib.sha256(content.encode('utf-8')).hexdigest() #我在校园22.4.17更新：加密方式为SHA256，格式为 province_timestamp_city

        sign_data = {
            "answers": '["0"]',
            "temperature": "36.0",
            "latitude": coordinate[1] + random_b,
            "longitude": coordinate[0] + random_a,
            "country": location_info['country'],
            "city": location_info['city'],
            "district": location_info['district'],
            "province": location_info['province'],
            "township": location_info['township'],
            "street": streetinfo['street'],
            "myArea": "",   # self.data['myArea'],
            "areacode": location_info['adcode'],
            "towncode": towncode,
            "citycode": "156" + city_code,
            "userId": "",
            "timestampHeader": sign_time,
            "signatureHeader": signature
        }
        data = urlencode(sign_data)
        response = self.session.post(url=url, data=data, headers=self.header)
        response = json.loads(response.text)
        # 打卡情况
        if response["code"] == 0:
            print("打卡成功")
            self.status_code = 1
        else:
            print("打卡失败")
            self.status_code = 0

    # 推送打卡结果
    def sendNotification(self):
        notify_time = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d-%H-%M')
        notify_result = self.getResult()
        # 如果开启了PushPlus
        if self.data['notification_type'] == "PushPlus":
            url = 'http://www.pushplus.plus/send'
            notify_token = self.data['notify_token']
            content = json.dumps({
                "打卡情况": notify_result,
                "打卡时间": notify_time
            }, ensure_ascii=False)
            msg = {
                "token": notify_token,
                "title": "⏰ 我在校园打卡结果通知",
                "content": content,
                "template": "json"
            }
            # 仅在失败情况下推送提醒
            if self.status_code != 1 and self.status_code != -1:
                requests.post(url, data=msg)
        elif self.data['notification_type'] == "DingDing":
            dingding = DingDingBot(self.data["dingding_access_token"],self.data['notify_token'])
            title = "⏰ 我在校园打卡结果通知"
            content = "## 我在校园打卡结果通知 \n" \
                      "打卡情况：{} \n \n " \
                      "打卡时间：{} \n".format(notify_result,notify_time)
            dingding.set_msg(title,content)
            # 仅在失败情况下推送提醒
            if self.status_code != 1 and self.status_code != -1:
                dingding.send()
        else:
            pass

    # 获取打卡结果
    def getResult(self):
        res = self.status_code
        if res == 1:
            return "✅ 打卡成功"
        elif res == 0:
            return "❌ 打卡失败，发生未知错误"
        elif res == 4:
            return "❌ 打卡失败，jwsession 失效"
        elif res == 5:
            return "❌ 打卡失败，登录错误，请检查账号信息"
        else:
            # 无事发生,不触发推送
            return "⭕"



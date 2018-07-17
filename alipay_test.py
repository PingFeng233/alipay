# -*- coding: utf-8 -*-

# pip install pycryptodome
__author__ = 'matrix'

from datetime import datetime
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from base64 import b64encode, b64decode
from urllib import quote_plus
from urlparse import urlparse,parse_qs
# from urllib.request import urlopen
from base64 import b64decode, b64encode

import json


class AliPay(object):
    """
    支付宝支付接口
    """

    def __init__(self, appid, app_notify_url, app_private_key_path,
                 alipay_public_key_path, return_url, debug=False):
        self.appid = appid
        self.app_notify_url = app_notify_url
        self.app_private_key_path = app_private_key_path
        self.app_private_key = None
        self.return_url = return_url
        with open(self.app_private_key_path) as fp:
            self.app_private_key = RSA.importKey(fp.read())

        self.alipay_public_key_path = alipay_public_key_path
        with open(self.alipay_public_key_path) as fp:
            self.alipay_public_key = RSA.importKey(fp.read())

        if debug is True:
            self.__gateway = "https://openapi.alipaydev.com/gateway.do"
        else:
            self.__gateway = "https://openapi.alipay.com/gateway.do"

    def direct_pay(self, subject, out_trade_no, total_amount, return_url=None, **kwargs):
        biz_content = {
            "subject": subject,
            "out_trade_no": out_trade_no,
            "total_amount": total_amount,
            "product_code": "FAST_INSTANT_TRADE_PAY",
            # "qr_pay_mode":4
        }

        biz_content.update(kwargs)
        data = self.build_body("alipay.trade.page.pay", biz_content, self.return_url)
        return self.sign_data(data)

    def build_body(self, method, biz_content, return_url=None):
        data = {
            "app_id": self.appid,
            "method": method,
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "biz_content": biz_content
        }

        if return_url is not None:
            data["notify_url"] = self.app_notify_url
            data["return_url"] = self.return_url

        return data

    def sign_data(self, data):
        data.pop("sign", None)
        # 排序后的字符串
        unsigned_items = self.ordered_data(data)
        unsigned_string = "&".join("{0}={1}".format(k, v) for k, v in unsigned_items)
        sign = self.sign(unsigned_string.encode("utf-8"))
        ordered_items = self.ordered_data(data)
        quoted_string = "&".join("{0}={1}".format(k, quote_plus(v)) for k, v in ordered_items)

        # 获得最终的订单信息字符串
        signed_string = quoted_string + "&sign=" + quote_plus(sign)
        return signed_string

    def ordered_data(self, data):
        complex_keys = []
        for key, value in data.items():
            if isinstance(value, dict):
                complex_keys.append(key)

        # 将字典类型的数据dump出来
        for key in complex_keys:
            data[key] = json.dumps(data[key], separators=(',', ':'))

        return sorted([(k, v) for k, v in data.items()])

    def sign(self, unsigned_string):
        # 开始计算签名
        key = self.app_private_key
        signer = PKCS1_v1_5.new(key)
        signature = signer.sign(SHA256.new(unsigned_string))
        # base64 编码，转换为unicode表示并移除回车
        sign = b64encode(signature).decode("utf8").replace("\n", "")
        return sign

    def _verify(self, raw_content, signature):
        # 开始计算签名
        key = self.alipay_public_key
        signer = PKCS1_v1_5.new(key)
        digest = SHA256.new()
        digest.update(raw_content.encode("utf8"))
        if signer.verify(digest, b64decode(signature.encode("utf8"))):
            return True
        return False

    def verify(self, data, signature):
        if "sign_type" in data:
            sign_type = data.pop("sign_type")
        # 排序后的字符串
        unsigned_items = self.ordered_data(data)
        message = "&".join(u"{}={}".format(k, v) for k, v in unsigned_items)
        return self._verify(message, signature)


if __name__ == "__main__":
    return_url = 'https://openapi.alipaydev.com/gateway.do?app_id=2016081900287577&biz_content=%7B%22total_amount%22%3A88.88%2C%22product_code%22%3A%22FAST_INSTANT_TRADE_PAY%22%2C%22out_trade_no%22%3A%22201702021222%22%2C%22subject%22%3A%22Iphone6+16G%22%7D&charset=utf-8&method=alipay.trade.page.pay&notify_url=http%3A%2F%2Fprojectsedus.com%2F&return_url=http%3A%2F%2F172.25.98.1%3A8080%2F&sign_type=RSA2&timestamp=2017-09-15+16%3A15%3A27&version=1.0&sign=ROovejoPtqJPJJy7Cmfry7ILMFgS8h9vy3OuagWNzlg9uk60aeIIDY71bP70QlPr5L83z%2F%2B91qQ3Lan%2FJVkIe7d3RnrJnjQ8lz5LTsw3HEgxHal8zvF5OXzRa6OoGupyD08l6V9aVyqH%2BjdU2Od6GNPdrtpmIMAVnDXzK3dS%2BqG1MWfqJkcEgshYsGm%2BMRdojrEfl4FtKrU0CM7uGtRPRzT3RaQQy7Kv5lGxOS4bM8WbbZUsApml8e7Ut2Hv6PuAXTJe7PRQvfN02cQyV8a2MSRXYZ0Ltap4WJOxJflSvhALH2SIIdyIelb1mvRFAkKZINgKobXNPm4Evyod%2Bb5jiQ%3D%3D'

    alipay = AliPay(
        appid="2016091900544963",
        app_notify_url="http://projectsedus.com/",
        app_private_key_path=u"/opt/odoo/test/payment_alipay/models/app_private_key.pem",
        alipay_public_key_path=u"/opt/odoo/test/payment_alipay/models/alipay_public_key.pem",
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        debug=True,  # 默认False,
        return_url="http://172.25.98.1:8080/alipay.trade.wap.pay-java-utf-8"
    )

    o = urlparse(return_url)
    query = parse_qs(o.query)
    processed_query = {}
    ali_sign = query.pop("sign")[0]
    for key, value in query.items():
        processed_query[key] = value[0]
    # print(alipay.verify(processed_query, ali_sign))

    url = alipay.direct_pay(
        subject="Iphone6 16G",
        out_trade_no="201702021222",
        total_amount=88.88
    )
    re_url = "https://openapi.alipaydev.com/gateway.do?{data}".format(data=url)
    # 沙箱环境下，用自己的账号是无法支付的，支付宝提供了沙箱账号、沙箱安卓App，进行测试支付
    print(re_url)
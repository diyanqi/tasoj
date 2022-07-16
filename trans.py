import requests
import time

def translate2(query):
    url = 'http://fanyi.youdao.com/translate'
    data = {
        "i": query,  # 待翻译的字符串
        "from": "AUTO",
        "to": "AUTO",
        "smartresult": "dict",
        "client": "fanyideskweb",
        "salt": "16081210430989",
        "doctype": "json",
        "version": "2.1",
        "keyfrom": "fanyi.web",
        "action": "FY_BY_CLICKBUTTION"
    }
    r = requests.post(url, data=data)
    print(r.text)
    res=r.json()
    time.sleep(1)
    return (res['translateResult'][0][0]['tgt'])  # 返回翻译后的结果

def translate3(content):
    url='https://cn.bing.com/ttranslatev3?isVertical=1&&IG=FFFF11FE1F4E4CD89E3312461FC1032B&IID=translator.5028.14' #请求地址
    headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'} #设置请求头
    post_data={'fromlang':'en','text':content,'to':'zh-Hans'} #设置请求参数
    result=requests.post(url,headers=headers).content.decode() #发出请求并将请求数据转换为str格式
    return (result)

def translate(source):
    from pygtrans import Translate
    client = Translate()
    # 翻译句子
    text = client.translate(source)
    return text.translatedText
    assert text.translatedText == '看这些图片，回答问题。'

    # 批量翻译
    texts = client.translate([
        'Good morning. What can I do for you?',
        'Read aloud and underline the sentences about booking a flight.',
        'May I have your name and telephone number?'
    ])
    assert [text.translatedText for text in texts] == [
        '早上好。我能为你做什么？', 
        '大声朗读并在有关预订航班的句子下划线。', 
        '可以给我你的名字和电话号码吗？'
    ]

    # 翻译到日语
    text = client.translate('请多多指教', target='ja')
    assert text.translatedText == 'お知らせ下さい'

    # 翻译到韩语
    text = client.translate('请多多指教', target='ko')
    assert text.translatedText == '조언 부탁드립니다'

    # 文本到语音
    tts = client.tts('やめて', target='ja')
    open('やめて.mp3', 'wb').write(tts)
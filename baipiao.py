from wsgiref import headers
from importlib_metadata import requires
import requests
import json
from xml.dom.minidom import *
import os
import shutil

c="PHPSESSID=cp6bdc65bvvm82eov2cu0e1oat"


def readf(path):
    with open(path,'r',encoding='utf-8') as f:
        return f.read()

def search_problem(q):
    li=get_problem_list()
    ret=[]
    for i in li:
        p=json.loads(readf("./problemset/"+i+"/problem.json"))
        if(p['title']==q):
            return True
    return False

def get_problem_old(fpsfile):
    dom=parse(fpsfile)
    data=dom.documentElement
    if(search_problem(data.getElementsByTagName('title')[0].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>",""))):
        print("同名题目已经存在！")
        return {"type":"wssb"}
    try:
        hintt=data.getElementsByTagName('hint')[0].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>","")
    except:
        hintt=''
    try:
        inputt=data.getElementsByTagName('input')[0].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>","")
    except:
        inputt=''
    try:
        outputt=data.getElementsByTagName('output')[0].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>","")
    except:
        outputt=''
    try:
        # print(data.getElementsByTagName('sample_input')[0].childNodes[0].nodeValue)
        sinput=data.getElementsByTagName('sample_input')[0].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>","")
        # print(sinput[0])
    except:
        sinput=''
    try:
        soutput=data.getElementsByTagName('sample_output')[0].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>","")
    except:
        soutput=''
    try:
        tagss=data.getElementsByTagName('source')[0].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>","").split(" ")
    except:
        tagss=['转载']
    ret={
        "title":data.getElementsByTagName('title')[0].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>",""),
        "type": "problem",
        "description": {
            "format": "html",
            "value": data.getElementsByTagName('description')[0].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>","")
        },
        "tags":tagss,
        "input_description": {
            "format": "html",
            "value":inputt
        },
        "output_description": {
            "format": "html",
            "value":outputt
        },
        "test_case_score": [
        ],
        "hint": {
            "format": "html",
            "value": hintt
        },
        "time_limit": int(data.getElementsByTagName('time_limit')[0].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>",""))*1000,
        "memory_limit":int(data.getElementsByTagName('memory_limit')[0].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>","")),
        "samples": [
            {
                "input":sinput,
                "output":soutput
            }
        ],
        "template": {},
        "spj": None,
        "rule_type": "OI",
        "source": "",
        "answers": [
            {
                "language": "Python3",
                "code": "print('Hello, world!')"
            }
        ]
    }
    return ret




def download_url(url, save_path, chunk_size=128):
    r = requests.get(url, stream=True,headers=({"Cookie":c}))
    with open(save_path, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            fd.write(chunk)

def get_data_list(path):
    file_dir=path
    for kk,dirs,kkk in os.walk(file_dir):
        return kkk

def savef(path,text):
    if(type(text) == dict):
        text=json.dumps(text)
    with open(path,'w',encoding='utf-8') as f:
        return f.write(text)

def get_problem_list():
    file_dir='./problemset'
    for kk,dirs,kkk in os.walk(file_dir):
        return dirs
def del_file(filepath):
    """
    删除某一目录下的所有文件或文件夹
    :param filepath: 路径
    :return:
    """
    del_list = os.listdir(filepath)
    for f in del_list:
        file_path = os.path.join(filepath, f)
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
def main(pid):
    fpsurl=f'http://tk.hustoj.com/problem_export_xml.php?pid={str(pid)}&fmt=fps'
    zero_buy=requests.get(url="http://tk.hustoj.com/pay.php?pid="+str(pid),headers=({"Cookie":c})) # 先0元购
    if(os.path.exists("./baipiao_test_box/"+str(pid)+".xml")):
        print("xml文档已存在")
    else:
        print("获取xml文档...",end='')
        download_url(url=fpsurl,save_path="./baipiao_test_box/"+str(pid)+".xml")
        print("done.")
    # print(fpsfile.text)
    print("解析xml文档...",end='')
    j=get_problem_old("./baipiao_test_box/"+str(pid)+".xml")
    if(j['type']=='wssb'):
        return
    print('done.')
    # print(j)
    if(os.path.exists("./baipiao_test_box/"+str(pid)+".zip")):
        print("已检测到预下载的测试数据，跳过下载")
    else:
        print("下载测试数据...",end='')
        zero_buy_data=requests.get(url="http://tk.hustoj.com/pay.php?fmt=zipdata&pid="+str(pid),headers=({"Cookie":c}))
        download_url(url=f"http://tk.hustoj.com/problem_export_xml.php?pid={str(pid)}&fmt=zipdata",save_path="./baipiao_test_box/"+str(pid)+".zip")
        print("done.")
    print("解压压缩包...")
    os.system(f"unzip -o ./baipiao_test_box/{str(pid)}.zip -d ./baipiao_test_box/{str(pid)}")
    print("done.\n储存题目",end="")
    li=get_data_list(f"./baipiao_test_box/{str(pid)}")
    # print('baipiao_test_box/'+str(pid))
    # print(li)
    amount=len(li)/2
    # print(amount)
    for i in li:
        if(i[-3:]=='out'):
            continue
        j['test_case_score'].append({
                "score": 10,
                "input_name": i,
                "output_name": i[:-3]+".out"
            })
    # print(j)
    new_problem_id=len(get_problem_list())+1000
    # new_problem_id=int(input("保存的题目id>>"))
    os.mkdir("./problemset/"+str(new_problem_id))
    os.mkdir("./problemset/"+str(new_problem_id)+"/testcase")
    savef("./problemset/"+str(new_problem_id)+"/problem.json",json.dumps(j))
    shutil.copyfile("./problem_temp_asmple/status.json","./problemset/"+str(new_problem_id)+"/status.json")
    for i in li:
        shutil.copyfile("./baipiao_test_box/"+str(pid)+"/"+i,"./problemset/"+str(new_problem_id)+"/testcase/"+i)
    os.remove("./baipiao_test_box/"+str(pid)+".zip")
    del_file(f"./baipiao_test_box/{str(pid)}")
    # os.removedirs(f"./baipiao_test_box/{str(pid)}")
    print("done.\n")
import _thread
if __name__=='__main__':
    while(1):
        pid=int(input(">>"))
        _thread.start_new_thread( main, (pid, ) )
# 将fps格式的题目转换成tasOJ格式的题目并保存
from wsgiref import headers
from importlib_metadata import requires
import requests
import json
from xml.dom.minidom import *
import os
import shutil
from random_word import RandomWords
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

def get_title(fpsfile):
    dom=parse(fpsfile)
    data=dom.documentElement
    return data.getElementsByTagName('title')[0].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>","")

def get_problem_old(fpsfile,savepid):
    dom=parse(fpsfile)
    data=dom.documentElement
    # if(search_problem(data.getElementsByTagName('title')[0].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>",""))):
    #     print("同名题目已经存在！")
    #     return {"type":"wssb"}
    try:
        hintt=data.getElementsByTagName('hint')[0].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>","").replace("&nbsp","&nbsp;")
    except:
        hintt=''
    try:
        inputt=data.getElementsByTagName('input')[0].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>","").replace("&nbsp","&nbsp;")
    except:
        inputt=''
    try:
        outputt=data.getElementsByTagName('output')[0].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>","").replace("&nbsp","&nbsp;")
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
        tagss=['TYVJ']
    kk=data.getElementsByTagName('description')[0].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>","")
    s=data.getElementsByTagName('description')[0].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>","")
    m=data.getElementsByTagName('description')[0].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>","")
    # try:
    ret={
            "title":str(RandomWords().get_random_word())+" "+str(RandomWords().get_random_word()),
            "type": "problem",
            "description": {
                "format": "html",
                "value": data.getElementsByTagName('description')[0].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>","").replace("&nbsp","&nbsp;")
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
            "time_limit": int(data.getElementsByTagName('time_limit')[-1].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>",""))*1000,
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
    # except Exception as e:
    #     print(e)
    #     return {"type":"wssb"}
    insample=data.getElementsByTagName('test_input')
    outsample=data.getElementsByTagName('test_output')
    # print(insample)
    os.mkdir("./problemset/"+str(savepid))
    os.mkdir("./problemset/"+str(savepid)+"/testcase/")
    # print((insample),(outsample))
    for i in range(0,min(len(insample),len(outsample))):
        ret['test_case_score'].append({
                "score": 10,
                "input_name": str(i+1)+".in",
                "output_name": str(i+1)+".out"
            })
        # print(insample[i].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>",""))
        try:
            savef("./problemset/"+str(savepid)+"/testcase/"+str(i+1)+".in",insample[i].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>",""))
        except:
            savef("./problemset/"+str(savepid)+"/testcase/"+str(i+1)+".in","")
        try:
            savef("./problemset/"+str(savepid)+"/testcase/"+str(i+1)+".out",outsample[i].childNodes[0].nodeValue.replace("<![CDATA[ ","").replace(" ]]>",""))
        except:
            savef("./problemset/"+str(savepid)+"/testcase/"+str(i+1)+".out","")
    savef("./problemset/"+str(savepid)+"/problem.json",json.dumps(ret))
    savef("./problemset/"+str(savepid)+"/status.json",json.dumps([{"value": 0, "name": "AC"}, {"value": 0, "name": "WA"}, {"value": 0, "name": "PA"}]))
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
def main():
    # fpspath=input("xml文档的位置>>")
    for i in range(1,25):# 27
        fpspath='./f1/fps_'+str(i)+".xml"
        # if(i%10==0):
        #     print(i)
        print("序号:",i,"  目标保存题号：",len(get_problem_list())+1000,"标题",get_title(fpspath),end='')
        # input("")
        # print("解析xml文档...",end='')
        j=get_problem_old(fpspath,len(get_problem_list())+1000)
        if(j['type']=='wssb'):
            return
        # print('done.')


if __name__=='__main__':
    main()
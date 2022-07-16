import requests
import json
import yaml
from lib import *

# 规定：脚本文件名称均为 scriptfile
# gcc,g++ 的-x参数一定要加，因为自动判断判断不出来
# cpp: g++ xxxxxxxx -x c++
#新增：change_script_name属性，在compile/run时使用，更改传入文件名
languages = {
    "python": {
        "compile": {
            "enable": False
        }, "run": {
            "enable": True,
            "cmd": ["/usr/bin/python3", "-u", "scriptfile"],
            "copyIn": None
        }
    },
    "pascal": {
        "compile": {
            "enable": True,
            "change_script_name":"scriptfile.pas",
            "cmd": ["/usr/bin/aarch64-linux-gnu-fpc-3.0.4","scriptfile.pas"],
            "compiled": "scriptfile"  # 编译结果，会记录fileid
        }, "run": {
            "enable": True,
            "cmd": ["./scriptfile"],
            "copyIn": "scriptfile"  # [lang].compile.compiled的值一样，不需要则None
        }
    },
    "cpp": {
        "compile": {
            "enable": True,
            "cmd": ["/usr/bin/g++","-x","c++" ,"scriptfile", "-o", "compiled","-Wall"],
            "compiled": "compiled"  # 编译结果，会记录fileid
        }, "run": {
            "enable": True,
            "cmd": ["./compiled"],
            "copyIn": "compiled"  # [lang].compile.compiled的值一样，不需要则None
        }
    },# /usr/bin/python3 /usr/bin/tobylang/tobylang.py run -f <filename>
    "tobylang":{ # py3
        "compile": {
            "enable": False,
        }, "run": {
            "enable": True,
            "cmd": ["/usr/bin/python3", "/usr/bin/tobylang/tobylang.py","run","-f","scriptfile"],
            "copyIn": None
        }
    },
    "tobylang-cpp":{
        "compile": {
            "enable": True,
            "cmd": "/usr/bin/python3 /usr/bin/tobylang/tobylang.py compile -f scriptfile -o compiled -c /usr/bin/g++".split(" "),
            "compiled": "compiled"  # 编译结果，会记录fileid
        }, "run": {
            "enable": True,
            "cmd": ["./compiled"],
            "copyIn": "compiled"  # [lang].compile.compiled的值一样，不需要则None
        }
    },
    "nodejs": {
        "compile": {
            "enable": False
        }, "run": {
            "enable": True,
            "cmd": ["/usr/bin/nodejs16/bin/node", "scriptfile"],
            "copyIn": None
        }
    },
    "wenyan": {
        "compile": {
            "enable": False
        }, "run": {
            "enable": True,
            "cmd": ["/usr/bin/nodejs16/bin/wenyan","scriptfile","--no-outputHanzi"],
            "copyIn": None
        }
    },
    # disabled
    "kotlin-jvm": {
        "compile": {
            "enable": True,
            "change_script_name":"scriptfile.kt", # kotlin要求文件后缀kt，所以特地加了这个属性（run也适用）
            "cmd": "/usr/bin/kotlinc/bin/kotlinc scriptfile.kt -jvm-target 11"\
                .split(" "),
            "compiled": "ScriptfileKt.class"  # 编译结果，会记录fileid
        }, "run": {
            "enable": True,
            "change_script_name":"scriptfile.kt",
            "cmd": "/usr/bin/kotlinc/bin/kotlin ScriptfileKt".split(" "),
            "copyIn": "ScriptfileKt.class"  # [lang].compile.compiled的值一样，不需要则None
        }
    },
    "openjdk-11":{
        "compile": {
            "enable": True,
            "change_script_name":"Oj.java", # kotlin要求文件后缀kt，所以特地加了这个属性（run也适用）
            "cmd": "/usr/lib/jvm/java-11-openjdk-arm64/bin/javac Oj.java"\
                .split(" "),
            "compiled": "Oj.class"
        }, "run": {
            "enable": True,
            "change_script_name":"Oj.java",
            "cmd": "/usr/lib/jvm/java-11-openjdk-arm64/bin/java Oj".split(" "),
            "copyIn": "Oj.class"  # [lang].compile.compiled的值一样，不需要则None
        }
    }
}
statShortNames={
    'Accepted':"AC",
    "Wrong Answer":"WA",
    'Memory Limit Exceeded':"MLE", 
    'Time Limit Exceeded':"TLE",
    'Output Limit Exceeded':"OLE",
    'File Error':"RE",
    'Nonzero Exit Status':"RE",
    'Signalled':"RE",
    'Internal Error':"RE",
    "Compile Error":"CE"
}
def antiSpaceAndEndl(string:str)->str:
    if(not string):
        return ""
    lines=string.splitlines()
    if(not lines[-1]):
        lines.pop()
    for i in range(len(lines)):
        lines[i]=lines[i].rstrip()
    nstring="\n".join(lines)
    return nstring

def compare(ofls,sfls)->bool:
    if len(ofls)==0 and len(sfls)!=0:
        return False
    for ofl, sfl in zip(ofls, sfls):
        if ofl != sfl:
            return False
    return True

def judge(code: str, lang: str, problem_id: str, form: dict, task_id: str, username: str)->dict:
    languageConf = languages[lang]

    # compile
    setstatus(task_id,{"status":"Compiling","problem_id":form['problem_id'],"language":form['language'],"username":username,"code":form['code']})
    compileConf = languageConf["compile"]
    compiled_id = ""
    if(compileConf["enable"]):
        cmd = compileConf["cmd"]
        print((compileConf["change_script_name"] if compileConf.get("change_script_name") else "scriptfile"))
        data = {
            "cmd": [{
                "args": cmd,  # 命令行参数
                "env": ["PATH=/usr/bin:/bin:/usr/bin/nodejs16/bin:/usr/lib/aarch64-linux-gnu/fpc/3.0.4"],
                "files": [{
                    "content": ""  # 输入数据，编译不用
                }, {
                    "name": "stdout",
                    "max": 10240
                }, {
                    "name": "stderr",
                    "max": 10240
                }],
                "cpuLimit": 20000000000,
                "memoryLimit": 10485760000,
                "stackLimit":20485760000,
                "procLimit": 60,
                "copyIn": {
                    (compileConf["change_script_name"] if compileConf.get("change_script_name") else "scriptfile"): {
                        "content": code
                    }
                },
                "copyOut": ["stdout", "stderr"],  # 需要明文返回的输入和报错流
                "copyOutCached": [compileConf["compiled"]],
                "copyOutDir": "1"
            }]
        }
        print((compileConf["change_script_name"] if compileConf.get("change_script_name") else "scriptfile"),compileConf["compiled"])
        compileres = requests.post(
            "http://localhost:5050/run", data=json.dumps(data)).json()[0]
        if(compileres["status"] != "Accepted"or compileres["exitStatus"] != 0):
            print(compileres)
            setstatus(task_id,{"status":"Compile Error","problem_id":form['problem_id'],"language":form['language'],"username":username,"code":form['code'],'msg':compileres['files']['stderr']})
            return {"status": "Compile Error", "shortStatus": "CE", "res": compileres}
        compiled_id = compileres["fileIds"][compileConf["compiled"]]

    # run
    p=get_problem(problem_id)
    timems=p['time_limit']
    memmb=p['memory_limit']
    setstatus(task_id,{"status":"Judging","problem_id":form['problem_id'],"language":form['language'],"username":username,"code":form['code']})
    grade=[]
    passed_numbers=0
    score=0
    fullscore=0
    test_numbers=0
    timens = int(timems*1000000*1.02)
    membyte = memmb*1024*1024  # 1MB=1024KB 1KB=1024B
    runConf = languageConf["run"]
    for i in p['test_case_score']:
        test_numbers+=1
        fullscore+=i['score']
        stdinput=readf("./problemset/"+str(problem_id)+"/testcase/"+i['input_name'])
        ansoutput=readf("./problemset/"+str(problem_id)+"/testcase/"+i['output_name'])
        if(runConf["enable"]):
            cmd = runConf["cmd"]
            copyInDict = {
                (runConf["change_script_name"] if runConf.get("change_script_name") else "scriptfile"): {
                    "content": code
                }
            }
            if(runConf["copyIn"]):
                copyInDict[runConf["copyIn"]]={"fileId":compiled_id}
            data = {
                "cmd": [{
                    "args": cmd,  # 命令行参数
                    "env": ["PATH=/usr/bin:/bin:/usr/bin/nodejs16/bin"],
                    "files": [{
                        "content": stdinput
                    }, {
                        "name": "stdout",
                        "max": 10240
                    }, {
                        "name": "stderr",
                        "max": 10240
                    }],
                    "cpuLimit": timens,
                    "memoryLimit": membyte,
                    "strictMemoryLimit": False,
                    "procLimit": 50,
                    "copyIn": copyInDict,
                    "copyOut": ["stdout", "stderr"],  # 需要明文返回的输入和报错流
                    "copyOutCached": [],
                    "copyOutDir": "1"
                }]
            }
            runres=requests.post("http://localhost:5050/run", data=json.dumps(data)).json()[0]
            # print(runres)
            if(runres["status"]!="Accepted"):
                # print(runres)
                grade.append({"testpoint":test_numbers,"status":runres["status"],"msg":runres['files']['stderr'],"time":runres['runTime'],"memory":runres['memory']})
                continue
                # return {"status": runres["status"], "shortStatus": statShortNames[runres["status"]], "res": runres}

            # judge
            ansoutput=antiSpaceAndEndl(ansoutput)
            output=antiSpaceAndEndl(runres["files"]["stdout"])
            # print(ansoutput,output)
            # compare有点小毛病？直接==吧
            if(ansoutput==output):
                grade.append({"testpoint":test_numbers,"status":"Accepted","msg":runres['files']['stderr'],"time":runres['runTime'],"memory":runres['memory']})
                passed_numbers+=1
                score+=i['score']
                # return {"status": "Accepted", "shortStatus": "AC", "res": runres}
            else:
                grade.append({"testpoint":test_numbers,"status":"Wrong Answer","msg":runres['files']['stderr'],"time":runres['runTime'],"memory":runres['memory']})
                # return {"status": "Wrong Answer", "shortStatus": "WA", "res": runres}
    if(passed_numbers==test_numbers): # 全通过
        return setstatus(task_id,{"status":"Accepted","problem_id":form['problem_id'],"language":form['language'],"username":username,"code":form['code'],'msg':'','testpoints':grade,'score':score,'scorerate':str(int(100*score/fullscore))+"%"})
    elif(passed_numbers==0): # 全错
        return setstatus(task_id,{"status":"Wrong Answer","problem_id":form['problem_id'],"language":form['language'],"username":username,"code":form['code'],'msg':'','testpoints':grade,'score':score,'scorerate':str(int(100*score/fullscore))+"%"})
    else: # 部分通过
        return setstatus(task_id,{"status":"Partial Accepted","problem_id":form['problem_id'],"language":form['language'],"username":username,"code":form['code'],'msg':'','testpoints':grade,'score':score,'scorerate':str(int(100*score/fullscore))+"%"})

# TLE
# print(judge("import time\ntime.sleep(2)\nprint('hi')","python",1000,256,"","hi\n"))
#AC
#print(judge("#include<iostream>\nusing namespace std;int main(){cout<<\"hi\"<<endl;return 0;}","cpp",1000,256,"","hi\n"))
#WA
#print(judge("#include<iostream>\nusing namespace std;int main(){cout<<\"hiaaaaaaaa\"<<endl;cout<<\"ahiaaaaaaaaaa\"<<endl;return 0;}","cpp",1000,256,"","hi\n"))
#CE
#print(judge("#include<iostream>\n这是一段会CE的代码~","cpp",1000,256,"","hi\n"))
#{'status': 'Compile Error', 'shortStatus': 'CE', 'res': {'status': 'Nonzero Exit Status', 'exitStatus': 1, 'time': 1106447498, 'memory': 51929088, 'runTime': 1109823818, 'files': {'stderr': "scriptfile:2:1: error: stray '\\350' in program\n    2 | 这是一段会CE的代码~\n      | ^\nscriptfile:2:2: error: stray '\\277' in program\n    2 | 这是一段会CE的代码~\n      |  ^\nscriptfile:2:3: error: stray '\\231' in program\n    2 | 这是一段会CE的代码~\n      |   ^\nscriptfile:2:4: error: stray '\\346' in program\n    2 | 这是一段会CE的代码~\n      |    ^\nscriptfile:2:5: error: stray '\\230' in program\n    2 | 这是一段会CE的代码~\n      |     ^\nscriptfile:2:6: error: stray '\\257' in program\n    2 | 这是一段会CE的代码~\n      |      ^\nscriptfile:2:7: error: stray '\\344' in program\n    2 | 这是一段会CE的代码~\n      |       ^\nscriptfile:2:8: error: stray '\\270' in program\n    2 | 这是一段会CE的代码~\n      |        ^\nscriptfile:2:9: error: stray '\\200' in program\n    2 | 这是一段会CE的代码~\n      |         ^\nscriptfile:2:10: error: stray '\\346' in program\n    2 | 这是一段会CE的代码~\n      |          ^\nscriptfile:2:11: error: stray '\\256' in program\n    2 | 这是一段会CE的代码~\n      |           ^\nscriptfile:2:12: error: stray '\\265' in program\n    2 | 这是一段会CE的代码~\n      |            ^\nscriptfile:2:13: error: stray '\\344' in program\n    2 | 这是一段会CE的代码~\n      |             ^\nscriptfile:2:14: error: stray '\\274' in program\n    2 | 这是一段会CE的代码~\n      |              ^\nscriptfile:2:15: error: stray '\\232' in program\n    2 | 这是一段会CE的代码~\n      |               ^\nscriptfile:2:18: error: stray '\\347' in program\n    2 | 这是一段会CE的代码~\n      |                  ^\nscriptfile:2:19: error: stray '\\232' in program\n    2 | 这是一段会CE的代码~\n      |                   ^\nscriptfile:2:20: error: stray '\\204' in program\n    2 | 这是一段会CE的代码~\n      |                    ^\nscriptfile:2:21: error: stray '\\344' in program\n    2 | 这是一段会CE的代码~\n      |                     ^\nscriptfile:2:22: error: stray '\\273' in program\n    2 | 这是一段会CE的代码~\n      |                      ^\nscriptfile:2:23: error: stray '\\243' in program\n    2 | 这是一段会CE的代码~\n      |                       ^\nscriptfile:2:24: error: stray '\\347' in program\n    2 | 这是一段会CE的代码~\n      |                        ^\nscriptfile:2:25: error: stray '\\240' in program\n    2 | 这是一段会CE的代码~\n      |                         ^\nscriptfile:2:26: error: stray '\\201' in program\n    2 | 这是一段会CE的代码~\n      |                          ^\nscriptfile:2:16: error: 'CE' does not name a type\n    2 | 这是一段会CE的代码~\n      |                ^~\n", 'stdout': ''}, 'fileError': [{'name': 'compiled', 'type': 'CopyOutOpen', 'message': 'open compiled: no such file or directory'}]}}
# 请读取res.files.stderr来获取报错信息

#OLE? 好像只会TLE 但是会有一个fileError 'fileError': [{'name': 'stdout', 'type': 'CollectSizeExceeded', 'message': 'Output Limit Exceeded'}]}}
#print(judge("while True:print('hihihihihihihihihihihihihihihihihihihihihihihihihihihihihihihihihihihihihihihihi')","python",1000,256,"","hi\n"))

#RE之类的没测




def iderun(code: str, lang: str, form: dict, task_id: str, username: str)->dict:
    languageConf = languages[lang]

    # compile
    # setstatus(task_id,{"status":"Compiling","problem_id":form['problem_id'],"language":form['language'],"username":username,"code":form['code']})
    compileConf = languageConf["compile"]
    compiled_id = ""
    if(compileConf["enable"]):
        cmd = compileConf["cmd"]
        print((compileConf["change_script_name"] if compileConf.get("change_script_name") else "scriptfile"))
        data = {
            "cmd": [{
                "args": cmd,  # 命令行参数
                "env": ["PATH=/usr/bin:/bin:/usr/bin/nodejs16/bin:/usr/lib/aarch64-linux-gnu/fpc/3.0.4"],
                "files": [{
                    "content": ""  # 输入数据，编译不用
                }, {
                    "name": "stdout",
                    "max": 10240
                }, {
                    "name": "stderr",
                    "max": 10240
                }],
                "cpuLimit": 20000000000,
                "memoryLimit": 10485760000,
                "stackLimit":20485760000,
                "procLimit": 60,
                "copyIn": {
                    (compileConf["change_script_name"] if compileConf.get("change_script_name") else "scriptfile"): {
                        "content": code
                    }
                },
                "copyOut": ["stdout", "stderr"],  # 需要明文返回的输入和报错流
                "copyOutCached": [compileConf["compiled"]],
                "copyOutDir": "1"
            }]
        }
        print((compileConf["change_script_name"] if compileConf.get("change_script_name") else "scriptfile"),compileConf["compiled"])
        compileres = requests.post(
            "http://localhost:5050/run", data=json.dumps(data)).json()[0]
        if(compileres["status"] != "Accepted" or compileres["exitStatus"] != 0):
            # print(compileres)
            # setstatus(task_id,{"status":"Compile Error","problem_id":form['problem_id'],"language":form['language'],"username":username,"code":form['code'],'msg':compileres['files']['stderr']})
            compileres['status']='Compile Error'
            return compileres
        compiled_id = compileres["fileIds"][compileConf["compiled"]]

    # run
    # p=get_problem(problem_id)
    # timems=p['time_limit']
    # memmb=p['memory_limit']
    # setstatus(task_id,{"status":"Judging","problem_id":form['problem_id'],"language":form['language'],"username":username,"code":form['code']})
    # grade=[]
    # passed_numbers=0
    # score=0
    # fullscore=0
    # test_numbers=0
    timens = int(5000*1000000*1.02)
    membyte = 512*1024*1024  # 1MB=1024KB 1KB=1024B
    runConf = languageConf["run"]
    # for i in p['test_case_score']:
        # test_numbers+=1
        # fullscore+=i['score']
    stdinput=form['stdinput']
    # ansoutput=readf("./problemset/"+str(problem_id)+"/testcase/"+i['output_name'])
    if(runConf["enable"]):
        cmd = runConf["cmd"]
        copyInDict = {
            (runConf["change_script_name"] if runConf.get("change_script_name") else "scriptfile"): {
                "content": code
            }
        }
        if(runConf["copyIn"]):
            copyInDict[runConf["copyIn"]]={"fileId":compiled_id}
        data = {
            "cmd": [{
                "args": cmd,  # 命令行参数
                "env": ["PATH=/usr/bin:/bin:/usr/bin/nodejs16/bin"],
                "files": [{
                    "content": stdinput
                }, {
                    "name": "stdout",
                    "max": 10240
                }, {
                    "name": "stderr",
                    "max": 10240
                }],
                "cpuLimit": timens,
                "memoryLimit": membyte,
                "strictMemoryLimit": False,
                "procLimit": 50,
                "copyIn": copyInDict,
                "copyOut": ["stdout", "stderr"],  # 需要明文返回的输入和报错流
                "copyOutCached": [],
                "copyOutDir": "1"
            }]
        }
        runres=requests.post("http://localhost:5050/run", data=json.dumps(data)).json()[0]
        # print(runres)
        return runres
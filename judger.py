import requests as req
import json
from lib import setstatus,readf,savef,get_problem
import os

def getTestNumbers(path):
    cnt=0
    f_list = os.listdir(path)
    for i in f_list:
        if os.path.splitext(i)[1]  == '.out':
            cnt+=1
    return cnt

def compare(ofls,sfls):
    if len(ofls)==0 and len(sfls)!=0:
        return 0
    for ofl, sfl in zip(ofls, sfls):
        if ofl != sfl:
            return 0
    return 10

def judge(code,language,problemid,task_id):
    if(language=='python'):
        grade=[] # 记录结果
        setstatus(task_id,{"status":"Judging"}) # 设置状态
        passed_numbers=0
        test_numbers=getTestNumbers('./problemset/'+str(problemid)+'/dataset')
        for i in range(test_numbers): # 一个个运行数据
            infile=readf('./problemset/'+str(problemid)+'/dataset'+'/'+str(i+1)+'.in')
            outfile=readf('./problemset/'+str(problemid)+'/dataset'+'/'+str(i+1)+'.out')
            res=run(code,language,None,infile)
            if(res[0]['status']=='Accepted'): # 运行成功
                if(compare(res[0]['files']['stdout'],outfile)): # 答案对比相同
                    grade.append({"testpoint":i+1,"status":"Accepted","msg":res[0]['files']['stderr'],"time":res[0]['time'],"memory":res[0]['memory']})
                    passed_numbers+=1
                else: # 答案对比不一样
                    grade.append({"testpoint":i+1,"status":"Wrong Answer","msg":res[0]['files']['stderr'],"time":res[0]['time'],"memory":res[0]['memory']})
            else:
                grade.append({"testpoint":i+1,"status":res[0]['status'],"msg":res[0]['files']['stderr'],"time":res[0]['time'],"memory":res[0]['memory']})
        if(passed_numbers==test_numbers): # 全通过
            return ({'status':'Accepted','msg':'','testpoints':grade,'score':100})
        elif(passed_numbers==0): # 全错
            return ({'status':'Wrong Answer','msg':'','testpoints':grade,'score':0})
        else:
            return ({'status':'Partial Accepted','msg':'','testpoints':grade,'score':int(passed_numbers/test_numbers)})
    elif(language=='cpp'):
        ret=comp(code,language) # 编译
        if(ret[0]['status']=='Accepted'): # 编译成功
            fileId=ret[0]['fileIds']['a'] # 获取程序id
            grade=[] # 记录结果
            setstatus(task_id,{"status":"Judging"}) # 设置状态
            passed_numbers=0
            test_numbers=getTestNumbers('./problemset/'+str(problemid)+'/dataset')
            for i in range(test_numbers): # 一个个运行数据
                infile=readf('./problemset/'+str(problemid)+'/dataset'+'/'+str(i+1)+'.in')
                outfile=readf('./problemset/'+str(problemid)+'/dataset'+'/'+str(i+1)+'.out')
                res=run(None,language,fileId,infile)
                if(res[0]['status']=='Accepted'): # 运行成功
                    if(compare(res[0]['files']['stdout'],outfile)): # 答案对比相同
                        grade.append({"testpoint":i+1,"status":"Accepted","msg":res[0]['files']['stderr'],"time":res[0]['time'],"memory":res[0]['memory']})
                        passed_numbers+=1
                    else: # 答案对比不一样
                        grade.append({"testpoint":i+1,"status":"Wrong Answer","msg":res[0]['files']['stderr'],"time":res[0]['time'],"memory":res[0]['memory']})
                else:
                    grade.append({"testpoint":i+1,"status":res[0]['status'],"msg":res[0]['files']['stderr'],"time":res[0]['time'],"memory":res[0]['memory']})
            if(passed_numbers==test_numbers): # 全通过
                return ({'status':'Accepted','msg':ret[0]['files']['stderr'],'testpoints':grade,'score':100})
            elif(passed_numbers==0): # 全错
                return ({'status':'Wrong Answer','msg':ret[0]['files']['stderr'],'testpoints':grade,'score':0})
            else:
                return ({'status':'Partial Accepted','msg':ret[0]['files']['stderr'],'testpoints':grade,'score':int(100*passed_numbers/test_numbers)})
        elif(ret[0]['status']=='Nonzero Exit Status'): # 编译报错
            return {'status':'Compile Error','msg':ret[0]['files']['stderr']}
        else: # 某些故意卡服务器编译的程序……（比如引入某个头文件可以导致编译器死循环）
            return {'status':ret[0]['status'],'msg':ret[0]['files']['stderr']}

def judge_cpp(fileId,pid,task_id,form,username):
    p=get_problem(pid)
    time_limit=p['time_limit']
    memory_limit=p['memory_limit']
    setstatus(task_id,{"status":"Judging","problem_id":form['problem_id'],"language":form['language'],"username":username,"code":form['code']})
    grade=[]
    passed_numbers=0
    score=0
    fullscore=0
    test_numbers=0
    for i in p['test_case_score']:
        test_numbers+=1
        fullscore+=i['score']
        res=runcpp(fileId,readf("./problemset/"+str(pid)+"/testcase/"+i['input_name']),time_limit,memory_limit)
        if(res[0]['status']=='Accepted'): # 运行成功
            if(compare(res[0]['files']['stdout'],readf("./problemset/"+str(pid)+"/testcase/"+i['output_name']))): # 答案对比相同
                grade.append({"testpoint":test_numbers,"status":"Accepted","msg":res[0]['files']['stderr'],"time":res[0]['time'],"memory":res[0]['memory']})
                passed_numbers+=1
                score+=i['score']
            else: # 答案对比不一样
                grade.append({"testpoint":test_numbers,"status":"Wrong Answer","msg":res[0]['files']['stderr'],"time":res[0]['time'],"memory":res[0]['memory']})
        else:
            grade.append({"testpoint":test_numbers,"status":res[0]['status'],"msg":res[0]['files']['stderr'],"time":res[0]['time'],"memory":res[0]['memory']})
    if(passed_numbers==test_numbers): # 全通过
        return setstatus(task_id,{"status":"Accepted","problem_id":form['problem_id'],"language":form['language'],"username":username,"code":form['code'],'msg':'','testpoints':grade,'score':score,'scorerate':str(int(100*score/fullscore))+"%"})
    elif(passed_numbers==0): # 全错
        return setstatus(task_id,{"status":"Wrong Answer","problem_id":form['problem_id'],"language":form['language'],"username":username,"code":form['code'],'msg':'','testpoints':grade,'score':score,'scorerate':str(int(100*score/fullscore))+"%"})
    else: # 部分通过
        return setstatus(task_id,{"status":"Partial Accepted","problem_id":form['problem_id'],"language":form['language'],"username":username,"code":form['code'],'msg':'','testpoints':grade,'score':score,'scorerate':str(int(100*score/fullscore))+"%"})

def run(code,language,fileId,content,mem=104857600):
    if(language=='python'):
        data={
            "cmd": [{
            "args": ["/usr/bin/python3", "1.py"],
            "env": ["PATH=/usr/bin:/bin"],
            "files": [{"content": content}, {"name": "stdout","max": 10240}, {"name": "stderr","max": 10240}],
            "cpuLimit": 3000000000,
            "clockLimit": 4000000000,
            "memoryLimit": mem,
            "procLimit": 50,
            "cpuRate": 0.1,
            "copyIn": {
                "1.py": {
                    "content":code
                }
            }}]
        }
        return req.post(url="http://localhost:5050/run",data=json.dumps(data)).json()
    elif(language=='cpp'):
        data={
            "cmd": [{
                "args": ["a"],
                "env": ["PATH=/usr/bin:/bin"],
                "files": [{
                    "content": content
                }, {
                    "name": "stdout",
                    "max": 10240
                }, {
                    "name": "stderr",
                    "max": 10240
                }],
                "cpuLimit": 10000000000,
                "memoryLimit": mem,
                "procLimit": 50,
                "strictMemoryLimit": False,
                "copyIn": {
                    "a": {
                        "fileId": fileId
                    }
                }
            }]
        }
        return req.post(url="http://localhost:5050/run",data=json.dumps(data)).json()

def comp(code,language):
    if(language=="cpp"):
        data={
            "cmd": [{
                "args": ["/usr/bin/g++", "a.cc", "-o", "a"],
                "env": ["PATH=/usr/bin:/bin"],
                "files": [{
                    "content": ""
                }, {
                    "name": "stdout",
                    "max": 10240
                }, {
                    "name": "stderr",
                    "max": 10240
                }],
                "cpuLimit": 10000000000,
                "memoryLimit": 1048576000,
                "procLimit": 50,
                "copyIn": {
                    "a.cc": {
                        "content":code
                    }
                },
                "copyOut": ["stdout", "stderr"],
                "copyOutCached": ["a.cc", "a"],
                "copyOutDir": "1"
            }]
        }
        return req.post(url="http://localhost:5050/run",data=json.dumps(data)).json()

def runcpp(fileId,content,t,m=512):
    data={"cmd":[{"args":["a"],"env":["PATH=/usr/bin:/bin"],"files":[{"content":content}, {"name": "stdout","max": 10240}, {"name": "stderr","max": 10240}],"cpuLimit": 10000000000,"memoryLimit": m*1024*512,"procLimit": 50,"strictMemoryLimit": False,"copyIn": {"a": {"fileId": fileId}}}]}
    return req.post(url="http://localhost:5050/run",data=json.dumps(data)).json()

def compile_cpp(code):
    data={
            "cmd": [{
                "args": ["/usr/bin/g++", "a.cc", "-o", "a"],
                "env": ["PATH=/usr/bin:/bin"],
                "files": [{
                    "content": ""
                }, {
                    "name": "stdout",
                    "max": 10240
                }, {
                    "name": "stderr",
                    "max": 10240
                }],
                "cpuLimit": 10000000000,
                "memoryLimit": 1048576000,
                "procLimit": 50,
                "copyIn": {
                    "a.cc": {
                        "content":code
                    }
                },
                "copyOut": ["stdout", "stderr"],
                "copyOutCached": ["a.cc", "a"],
                "copyOutDir": "1"
            }]
        }
    return req.post(url="http://localhost:5050/run",data=json.dumps(data)).json()
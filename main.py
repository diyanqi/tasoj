import _thread
import base64
from crypt import methods
import datetime as dt
import html
import string
import time
from datetime import timedelta
from functools import cmp_to_key
from io import BytesIO
from queue import Queue
from xml.dom.minidom import parseString
import os
import zipfile
import email_validator
from flask import *
from flask_bootstrap import *
from flask_wtf import *
from wtforms import *
from wtforms.validators import *

import judger
import onlyJudger
from captcha import *
from lib import *
from tasoj_env import *
from trans import *

# screen -r 3784748.realtasojserver

class LoginForm(FlaskForm):
    email = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    verify_code = StringField('验证码', validators=[DataRequired()])
    remember_me = BooleanField('记住自己的用户')
    submit = SubmitField('登录')

app = Flask(__name__)
app.config['SECRET_KEY'] = "103928394839202839582034"
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=3) # 配置3天有效
bootstrap = Bootstrap(app)

judgeQ=Queue(maxsize=0)

def ide_throw_to_judge(task_id,form,username):
    if(not form['language'] in SUPPORT_LANGUAGE_IDS):
        return
    res=onlyJudger.iderun(code=form['code'],lang=form['language'],form=form,task_id=str(task_id),username=username)
    savef("./ide_run_result/"+str(task_id)+".json",json.dumps(res))

def throw_to_judge(task_id,form,username):
    if(not form['language'] in SUPPORT_LANGUAGE_IDS):
        return
    # 进入测评队列
    setstatus(task_id,{"status":"Waiting","problem_id":form['problem_id'],"language":form['language'],"username":username,"code":form['code']})
    # 分配到资源
    onlyJudger.judge(code=form['code'],lang=form['language'],problem_id=form['problem_id'],form=form,task_id=str(task_id),username=username)
    trainjson=json.loads(readf('./users/'+email2usrid(username)+'/train.json'))
    projson=json.loads(readf('./problemset/'+str(form['problem_id'])+'/status.json'))
    j=json.loads(readf('./judgements/'+str(task_id)+".json"))
    # user trainning
    if(j['status']=='Accepted'):
        if(form['problem_id'] not in trainjson['passed']):
            trainjson['passed'].append(form['problem_id'])
        if(form['problem_id'] in trainjson['tried']):
            trainjson['tried'].remove(form['problem_id'])
    else:
        if(form['problem_id'] not in trainjson['tried']):
            if(form['problem_id'] not in trainjson['passed']):
                trainjson['tried'].append(form['problem_id'])
    # problem counting
    if(j['status']=='Accepted'):
        for i in projson:
            if(i["name"]=="AC"):
                i['value']+=1
                break
    elif(j['status']=='Wrong Answer'):
        for i in projson:
            if(i["name"]=="WA"):
                i['value']+=1
                break
    elif(j['status']=='Partial Accepted'):
        for i in projson:
            if(i["name"]=="PA"):
                i['value']+=1
                break
    savef("./users/"+email2usrid(username)+'/train.json',json.dumps(trainjson))
    savef("./problemset/"+str(form['problem_id'])+'/status.json',json.dumps(projson))

def throw_to_judge_contest(task_id,form,username):
    if(not form['language'] in SUPPORT_LANGUAGE_IDS):
        return
    # 进入测评队列
    setstatus(task_id,{"status":"Waiting","problem_id":form['problem_id'],"language":form['language'],"username":username,"code":form['code']})
    # 分配到资源
    onlyJudger.judge(code=form['code'],lang=form['language'],problem_id=form['problem_id'],form=form,task_id=str(task_id),username=username)
    trainjson=json.loads(readf('./users/'+email2usrid(username)+'/train.json'))
    projson=json.loads(readf('./problemset/'+str(form['problem_id'])+'/status.json'))
    j=json.loads(readf('./judgements/'+str(task_id)+".json"))
    conj=json.loads(readf(f"./contest/{form['contest_id']}.json"))
    conj['rank'][username][str(form['problem_id'])]['tried_times']+=1
    conj['rank'][username][str(form['problem_id'])]['score']=max(conj['rank'][username][str(form['problem_id'])]['score'],j['score'])
    savef(f"./contest/{form['contest_id']}.json",json.dumps(conj))
    # user trainning
    if(j['status']=='Accepted'):
        if(form['problem_id'] not in trainjson['passed']):
            trainjson['passed'].append(form['problem_id'])
        if(form['problem_id'] in trainjson['tried']):
            trainjson['tried'].remove(form['problem_id'])
    else:
        if(form['problem_id'] not in trainjson['tried']):
            if(form['problem_id'] not in trainjson['passed']):
                trainjson['tried'].append(form['problem_id'])
    # problem counting
    if(j['status']=='Accepted'):
        for i in projson:
            if(i["name"]=="AC"):
                i['value']+=1
                break
    elif(j['status']=='Wrong Answer'):
        for i in projson:
            if(i["name"]=="WA"):
                i['value']+=1
                break
    elif(j['status']=='Partial Accepted'):
        for i in projson:
            if(i["name"]=="PA"):
                i['value']+=1
                break
    savef("./users/"+email2usrid(username)+'/train.json',json.dumps(trainjson))
    savef("./problemset/"+str(form['problem_id'])+'/status.json',json.dumps(projson))

@app.route("/follow/<userid>")
def follow(userid):
    username=(get_username(session.get("logincookie")))
    if(username==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
    real_follow(username,userid2email(userid))
    return json.dumps({"status":"succeed"})
@app.before_request
def before_req():
    return antiSpider(request) #过滤爬虫，去lib.py编辑反爬逻辑
@app.route("/random/problem")
def random_problem():
    probid=get_random_problem()
    return safe_redirect(f"/problem/{probid}")

@app.route("/unfollow/<userid>")
def unfollow(userid):
    username=(get_username(session.get("logincookie")))
    if(username==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
    real_unfollow(username,userid2email(userid))
    return json.dumps({"status":"succeed"})

@app.route('/unread_number')
def unread_number():
    username=(get_username(session.get("logincookie")))
    if(username==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
    return str(len(get_noti(email2usrid(username))['unread']))

@app.route('/private/<userid>')
def private(userid):
    print(userid)
    return readf('./static/temp.html').replace('<!-- title -->','私信').replace('<!-- documents -->',readf('./static/private.html'))

@app.route('/search')
def search():
    q=request.args.get("q")
    if(q==None):
        return readf('./static/temp.html').replace('<!-- title -->','聚合搜索').replace('<!-- documents -->',readf('./static/search.html')).replace("(value!!!)","")
    start_time=time.time()
    problemlist=search_problem(q)
    problemhtml=''
    cnt=0
    for i in problemlist:
        cnt+=1
        problemhtml+=f'''<tr onclick="window.open('/problem/{i['problemid']}');" style="cursor:pointer;"><td></td><td>{i['problemid']}</td><td>{i['title']}</td><td>{merge_tag(i['tags'])}</td><td>{ac_rate(i['problemid'])}</td></tr>'''
    end_time=time.time()
    print("problem_search_delay=",end_time-start_time)
    start_time=time.time()
    judgementlist=search_judgement(q)
    judgementhtml=''
    cnt=0
    for i in judgementlist:
        cnt+=1
        judgementhtml+=f'''<tr onclick="window.location='/judgements/{str(i['judgeid'])}'" 
        style="cursor:pointer;"><td><div class="mdui-chip mdui-color-{COLOR(i['status'])}"><span class="mdui-chip-title">{i['status']}</span></div></td>
        <td>{time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(float(i['judgeid'])))}</td>
        <td>{str(i['problem_id'])}</td>
        <td>{i['language']}</td>
        <td>{email2nickname(i['username'])}</td></tr>'''
    end_time=time.time()
    print("judgement_search_delay=",end_time-start_time)
    start_time=time.time()
    asklist=search_ask(q)
    askhtml=''
    cnt=0
    for i in asklist:
        cnt+=1
        askhtml+=f'''<tr onclick="window.location='/ask/{i['askid']}'" style="cursor:pointer;"><td>{str(cnt)}</td><td>{time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(i['time']))}</td><td>{i['title']}</td><td>{email2nickname(i['email'])}</td></tr>'''
    end_time=time.time()
    print("ask_search_delay=",end_time-start_time)
    start_time=time.time()
    artlist=search_art(q)
    arthtml=''
    cnt=0
    for i in artlist:
        cnt+=1
        arthtml+=f'''<tr onclick="window.location='/article/{i['askid']}'" style="cursor:pointer;"><td>{str(cnt)}</td><td>{time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(i['time']))}</td><td>{i['title']}</td><td>{email2nickname(i['email'])}</td></tr>'''
    end_time=time.time()
    print("art_search_delay=",end_time-start_time)
    # start_time=time.time()
    # ulist=search_user(q)
    # uhtml=''
    # cnt=0
    # for i in ulist:
    #     cnt+=1
    #     uhtml+=f'''<tr onclick="window.location='/user/{i['userid']}'" style="cursor:pointer;"><td>{str(cnt)}</td><td>{i['userid']}</td><td>{email2nickname(userid2email(i['userid']))}</td><td>{get_oneword_byemail(userid2email(i['userid']))}</td></tr>'''
    # endtime=time.time()
    # print("user_search_delay=",endtime-start_time)
    return readf('./static/temp.html').replace('<!-- title -->','聚合搜索').replace('<!-- documents -->',readf('./static/search.html')).replace("(value!!!)",q).replace("<!-- problemlist -->",problemhtml).replace("<!-- judgelist -->",judgementhtml).replace("<!-- asklist -->",askhtml).replace("<!-- artlist -->",arthtml)#.replace("<!-- ulist -->",uhtml)

@app.route('/notifications')
def notifications():
    username=(get_username(session.get("logincookie")))
    if(username==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
    userid=email2usrid(username)
    t=''
    page=request.args.get("page")
    if(page==None):
        page=1
    page=int(page)
    cnt=0
    for i in get_noti(userid)['unread']:
        cnt+=1
        if(cnt>page*10):
            break
        if(cnt<=(page-1)*10):
            continue
        text=i['msg']
        try:
            text=json.loads(text)
            #print(text)
            text=text["msg"]
        except Exception as e:
            #print("文本信息",text,str(e))
            pass
        t+=f'''<tr class="mdui-table-row-selected">
        <td><i>{cnt}</i></td>
        <td><i>{time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(i['time']))}</i></td>
        <td><i>{i['type']}</i></td>
        <td><i>{text}</i></td>
        <td><a href="{i['link']}"><i>{i['link']}</i></a></td>
        </tr>'''
        # t+=f'''<div class="mdui-list-item mdui-ripple" href="{i['link']}">
        #     <div class="mdui-list-item-content">
        #         <div class="mdui-list-item-title mdui-list-item-one-line">{i['type']} #{cnt}</div>
        #         <div class="mdui-list-item-text mdui-list-item-three-line">{text}<br/>{i['link']}<br/>time: {time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(i['time']))}</div>
        #     </div>
        # </div>'''
    for i in get_noti(userid)['read']:
        cnt+=1
        if(cnt>page*10):
            break
        if(cnt<=(page-1)*10):
            continue
        text=i['msg']
        try:
            text=json.loads(text)["msg"]
        except Exception as e:
            #print("文本信息",text,str(e))
            pass
        t+=f'''<tr>
        <td>{cnt}</td>
        <td>{time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(i['time']))}</td>
        <td>{i['type']}</td>
        <td>{text}</td>
        <td><a href="{i['link']}">{i['link']}</a></td>
        </tr>'''
        # t+=f'''<div class="mdui-list-item mdui-ripple" href="{i['link']}">
        #     <div class="mdui-list-item-content">
        #         <div class="mdui-list-item-title mdui-list-item-one-line">{i['type']} #{cnt}</div>
        #         <div class="mdui-list-item-text mdui-list-item-two-line">{text}<br/>time: {time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(i['time']))} {i['link']}</div>
        #     </div>
        # </div>'''
    read_all(userid)
    return readf('./static/temp.html').replace('<!-- title -->','通知中心').replace('<!-- documents -->',readf('./static/notifications.html')).replace("<!-- lists -->",t)

@app.route('/settings')
def settings():
    username=(get_username(session.get("logincookie")))
    if(username==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
    username=email2usrid(username)
    oneword=json.loads(readf("./users/"+(username)+"/profile.json"))['oneword']
    return readf('./static/temp.html').replace('<!-- title -->','个人设置').replace('<!-- documents -->',readf('./static/settings.html')).replace('(username)',username).replace("(oneword_text)",oneword).replace("(md)",readf("./users/"+username+"/introduction.md"))

@app.route('/user/save_profilemd',methods=['POST'])
def user_save_profilemd():
    username=get_username(session.get("logincookie"))
    if(username==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
    username=email2usrid(username)
    savef("./users/"+username+"/introduction.md",request.get_json()['msg'])
    return json.dumps({"status":"success"})

@app.route('/user/save_oneword',methods=['POST'])
def user_save_oneword():
    username=get_username(session.get("logincookie"))
    if(username==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
    username=email2usrid(username)
    j=json.loads(readf("./users/"+username+"/profile.json"))
    if(len(request.get_json()['msg'])>33):
        return json.dumps({"status":"failed"})
    j['oneword']=html.escape(request.get_json()['msg'])
    savef("./users/"+username+"/profile.json",json.dumps(j))
    return json.dumps({"status":"success"})

@app.route('/getImg/',methods=['GET','POST']) # 用户头像上传
def getImg():
    username=get_username(session.get("logincookie"))
    if(username==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
    username=email2usrid(username)
    imgData = request.files["image"]
    path = "./users/"+username+"/"
    imgName = imgData.filename
    imgName=imgName[:imgName.rfind('.')]+'.png'
    imgName="avatar.png"
    file_path = path + imgName
    imgData.save(file_path)
    url = "./users/"+username+"/" + imgName
    return '''<script>location.href="/settings"</script>'''

@app.route('/send_benben',methods=['POST'])
def send_benben():
    username=get_username(session.get("logincookie"))
    if(username==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
    if(get_activity_delta(username)<=5):
        return jsonify({'status':'too_fast'})
    record_activity(username)
    new_benben(username=username,md=request.get_json()['msg'])
    return json.dumps({"status":"success"})

@app.route('/helpful',methods=['POST']) # 有用
def helpful():
    username=get_username(session.get("logincookie"))
    if(username==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
    if(get_activity_delta(username)<=5):
        return jsonify({'status':'too_fast'})
    record_activity(username)
    form=request.get_json()
    j=json.loads(readf("./article/psg/"+str(form['askid'])+".json"))
    if(not username in j['samers']):
        j['the_same']+=1
        j['samers'].append(username)
        savef(("./article/psg/"+str(form['askid'])+".json"),json.dumps(j))
        uid=get_profile(session.get("logincookie"))["userid"]
        msg={"user":email2nickname(username),"msg":f'<a href="/user/{uid}">{email2nickname(username)}</a> 给你的文章点了有用>>'}
        send_notice(email2usrid(j['email']),"有用",time.time(),json.dumps(msg),"/article/"+form['askid'])
        return json.dumps({"status":"success"})
    else:
        return json.dumps({"status":"failed"})

@app.route('/the_same',methods=['POST']) # 同问
def the_same():
    username=get_username(session.get("logincookie"))
    if(username==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
    if(get_activity_delta(username)<=5):
        return jsonify({'status':'too_fast'})
    record_activity(username)
    form=request.get_json()
    j=json.loads(readf("./ask/aq/"+str(form['askid'])+".json"))
    if(not username in j['samers']):
        j['the_same']+=1
        j['samers'].append(username)
        savef(("./ask/aq/"+str(form['askid'])+".json"),json.dumps(j))
        uid=get_profile(session.get("logincookie"))["userid"]
        msg={"user":email2nickname(username),"msg":f'<a href="/user/{uid}">{email2nickname(username)}</a> 和你有同样的疑惑>>'}
        send_notice(email2usrid(j['email']),"同问",time.time(),json.dumps(msg),"/ask/"+form['askid'])
        return json.dumps({"status":"success"})
    else:
        return json.dumps({"status":"failed"})

@app.route("/new_ques",methods=['POST'])
def new_ques():
    username=get_username(session.get("logincookie"))
    if(username==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
    if(get_activity_delta(username)<=5):
        return jsonify({'status':'too_fast'})
    record_activity(username)
    form=request.get_json() # problem_id&msg&title
    j={"email":username,"title":form['title'],"question":form['msg'],"time":time.time(),"the_same":0,"samers":[],"answers":[],"pid":form['problem_id']}
    kk=json.loads(readf("./ask/config.json"))
    kk['amount']+=1
    savef("./ask/config.json",json.dumps(kk))
    savef("./ask/aq/"+str(kk['amount'])+".json",json.dumps(j))
    return json.dumps({"status":"success"})

@app.route('/the_answer',methods=['POST'])
def the_answer():
    username=get_username(session.get("logincookie"))# email!!!
    if(username==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
    if(get_activity_delta(username)<=5):
        return jsonify({'status':'too_fast'})
    record_activity(username)
    form=request.get_json() # askid&msg
    j=json.loads(readf("./ask/aq/"+str(form['askid'])+".json"))
    j['answers'].append({"email":username,"answer":form['msg'],"time":time.time(),"liked":0,"likers":[],"aid":len(j['answers'])+1})
    savef(("./ask/aq/"+str(form['askid'])+".json"),json.dumps(j))
    uid=get_profile(session.get("logincookie"))["userid"]
    msg={"user":email2nickname(username),"msg":f'<a href="/user/{uid}">{email2nickname(username)}</a> 解答了你的疑惑>>'}
    send_notice(email2usrid(j['email']),"回答",time.time(),json.dumps(msg),"/ask/"+form['askid'])
    return json.dumps({"status":"success"})

@app.route('/the_like',methods=['POST']) # 赞同
def the_like():
    username=get_username(session.get("logincookie"))
    if(username==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
    if(get_activity_delta(username)<=5):
        return jsonify({'status':'too_fast'})
    record_activity(username)
    form=request.get_json()
    j=json.loads(readf("./ask/aq/"+str(form['askid'])+".json"))
    for i in j['answers']:
        if(str(i['aid'])==form['aid']):
            if(not username in i['likers']):
                i['likers'].append(username)
                i['liked']+=1
                savef(("./ask/aq/"+str(form['askid'])+".json"),json.dumps(j))
                uid=get_profile(session.get("logincookie"))["userid"]
                msg={"user":email2nickname(username),"msg":f'<a href="/user/{uid}">{email2nickname(username)}</a> 赞同了你的回答>>'}
                send_notice(email2usrid(j['email']),"赞同",time.time(),json.dumps(msg),"/ask/"+form['aid'])
                return json.dumps({"status":"success"})
    return json.dumps({"status":"failed"})

@app.route('/ask/<askid>')
def ask(askid):
    if(askid=='list'):
        email=get_username(session.get("logincookie"))
        if(email==None):
            return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
        page=request.args.get("page")
        if(page==None):
            page=1
        page=int(page)
        li=get_ask_list()
        li = sort_humanly(li)
        li.reverse()
        t=''
        cnt=0
        for i in li:
            cnt+=1
            if(cnt>page*10):
                break
            if(cnt<=(page-1)*10):
                continue
            kk=json.loads(readf("./ask/aq/"+i))
            t+='''<tr onclick="window.location='/ask/{}'" style="cursor:pointer;"><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'''.format(i[:-5],i[:-5],html.escape(kk['title']),email2nickname(kk['email']),time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(kk['time'])),len(kk['answers']))
        return readf('./static/temp.html').replace('<!-- title -->','问答').replace('<!-- documents -->',readf('./static/ask_list.html')).replace("<!-- lists -->",t)
    else:
        username=get_username(session.get("logincookie"))
        if(username==None):
            return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
        if(not os.path.exists('./ask/aq/'+askid+'.json')):
            return abort(404)
        bb=json.loads(readf('./ask/aq/'+askid+'.json'))
        if(bb['pid']=="0"):
            pk=""
        else:
            pk=f'''<a class="mdui-btn mdui-ripple" href="/problem/{bb['pid']}">有关问题：P{bb['pid']}</a>'''
        t=''
        cnt=0
        bb['answers'].sort(key=cmp_to_key(lambda a, b: b['liked']-a['liked']))
        # bb.answers 排序...
        for i in bb['answers']:
            cnt+=1
            t+=f'''
<div class="mdui-card">
    <!-- 卡片头部，包含头像、标题、副标题 -->
    <div class="mdui-card-header">
      <img class="mdui-card-header-avatar" src="{"/users_byid/"+email2usrid(i['email'])+"/avatar.png"}"/>
      <div class="mdui-card-header-title"><a href="/user/{email2usrid(i['email'])}">{email2nickname(i['email'])}</a></div>
      <div class="mdui-card-header-subtitle">{get_oneword_byemail(i['email'])}</div>
    </div>
      <div class="mdui-card-header-subtitle">{time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(i['time']))}</div>
    
    <!-- 卡片的内容 -->
    <div class="mdui-card-content">
        <div id="test-editormd-view-{str(cnt)}" class="mdui-typo">
            <pre class="nohighlight" id="test-editormd-markdown-doc-{str(cnt)}">{escape(i['answer'])}</pre>
        </div>
    </div>
  
    <!-- 卡片的按钮 -->
    <div class="mdui-card-actions">
      <button class="mdui-btn mdui-ripple" onclick="likeit('{i['aid']}');">赞同：{i['liked']}</button>
      <button class="mdui-btn mdui-btn-icon mdui-float-right">
        <i class="mdui-icon material-icons">expand_more</i>
      </button>
    </div>
  
  </div><script>
        $(()=>{{
            var md=document.getElementById("test-editormd-markdown-doc-{str(cnt)}").innerText;
            markdown_render_dom(document.getElementById("test-editormd-view-{str(cnt)}"), md);
        }})
    </script><br>'''
        return readf('./static/temp.html').replace('<!-- title -->','问答').replace('<!-- documents -->',readf('./static/ask_temp.html')).replace("<!-- problemkkk -->",pk).replace("(userid!!!)",email2usrid(bb['email'])).replace("avatar.jpg","/users_byid/"+email2usrid(bb['email'])+"/avatar.png").replace("<!-- asker -->",email2nickname(bb['email'])).replace("<!-- asker_oneword -->",get_oneword_byemail(bb['email'])).replace("<!-- title -->",bb['title']).replace("<!-- time -->",time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(bb['time']))).replace("<!-- the_same -->",str(bb['the_same'])).replace("<!-- question -->",escape(bb['question'])).replace("<!-- answers -->",t)

@app.route("/new_pas",methods=['POST'])
def new_pas():
    username=get_username(session.get("logincookie"))
    if(username==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
    if(get_activity_delta(username)<=5):
        return jsonify({'status':'too_fast'})
    record_activity(username)
    form=request.get_json() # problem_id&msg&title
    j={"email":username,"title":form['title'],"question":form['msg'],"time":time.time(),"the_same":0,"samers":[],"answers":[],"pid":form['problem_id']}
    kk=json.loads(readf("./article/config.json"))
    kk['amount']+=1
    savef("./article/config.json",json.dumps(kk))
    savef("./article/psg/"+str(kk['amount'])+".json",json.dumps(j))
    return json.dumps({"status":"success"})

@app.route('/the_comment',methods=['POST'])
def the_comment():
    username=get_username(session.get("logincookie"))
    if(username==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
    if(get_activity_delta(username)<=5):
        return jsonify({'status':'too_fast'})
    record_activity(username)
    form=request.get_json() # askid&msg
    j=json.loads(readf("./article/psg/"+str(form['askid'])+".json"))
    j['answers'].append({"email":username,"answer":form['msg'],"time":time.time(),"liked":0,"likers":[],"aid":len(j['answers'])+1})
    savef(("./article/psg/"+str(form['askid'])+".json"),json.dumps(j))
    uid=get_profile(session.get("logincookie"))["userid"]
    msg={"user":email2nickname(username),"msg":f'<a href="/user/{uid}">{email2nickname(username)}</a> 有人评论了你的文章>>'}
    send_notice(email2usrid(j['email']),"评论",time.time(),json.dumps(msg),"/article/"+form['askid'])
    return json.dumps({"status":"success"})

@app.route('/art_like',methods=['POST']) # 点赞
def art_like():
    username=get_username(session.get("logincookie"))
    if(username==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
    if(get_activity_delta(username)<=5):
        return jsonify({'status':'too_fast'})
    record_activity(username)
    form=request.get_json()
    j=json.loads(readf("./article/psg/"+str(form['askid'])+".json"))
    for i in j['answers']:
        if(str(i['aid'])==form['aid']):
            if(not username in i['likers']):
                i['likers'].append(username)
                i['liked']+=1
                savef(("./article/psg/"+str(form['askid'])+".json"),json.dumps(j))
                uid=get_profile(session.get("logincookie"))["userid"]
                msg={"user":email2nickname(username),"msg":f'<a href="/user/{uid}">{email2nickname(username)}</a> 给你的评论点了赞>>'}
                send_notice(email2usrid(j['email']),"点赞",time.time(),json.dumps(msg),"/article/"+form['aid'])
                return json.dumps({"status":"success"})
    return json.dumps({"status":"failed"})

@app.route("/demo/md")
def demo_md():
    return readf("./markdown-tasoj.html")

@app.route('/article/<askid>')
def article(askid):
    if(askid=='list'):
        email=get_username(session.get("logincookie"))
        if(email==None):
            return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
        page=request.args.get("page")
        if(page==None):
            page=1
        page=int(page)
        li=get_art_list()
        li = sort_humanly(li)
        li.reverse()
        t=''
        cnt=0
        for i in li:
            cnt+=1
            if(cnt>page*10):
                break
            if(cnt<=(page-1)*10):
                continue
            kk=json.loads(readf("./article/psg/"+i))
            t+='''<tr onclick="window.location='/article/{}'" style="cursor:pointer;"><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'''.format(i[:-5],i[:-5],html.escape(kk['title']),email2nickname(kk['email']),time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(kk['time'])),len(kk['answers']))
        return readf('./static/temp.html').replace('<!-- title -->','文章').replace('<!-- documents -->',readf('./static/article_list.html')).replace("<!-- lists -->",t)
    else:
        username=get_username(session.get("logincookie"))
        if(username==None):
            return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
        bb=json.loads(readf('./article/psg/'+askid+'.json'))
        if(bb['pid']=="0"):
            pk=""
        else:
            pk=f'''<a class="mdui-btn mdui-ripple" href="/problem/{bb['pid']}">有关问题：P{bb['pid']}</a>'''
        t=''
        cnt=0
        bb['answers'].sort(key=cmp_to_key(lambda a, b: b['liked']-a['liked']))
        # bb.answers 排序...
        for i in bb['answers']:
            cnt+=1
            t+=f'''
<div class="mdui-card">

    <!-- 卡片头部，包含头像、标题、副标题 -->
    <div class="mdui-card-header">
      <img class="mdui-card-header-avatar" src="{"/users_byid/"+email2usrid(i['email'])+"/avatar.png"}"/>
      <div class="mdui-card-header-title"><a href="/user/{email2usrid(i['email'])}">{email2nickname(i['email'])}</a></div>
      <div class="mdui-card-header-subtitle">{get_oneword_byemail(i['email'])}</div>
    </div>
      <div class="mdui-card-header-subtitle">{time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(i['time']))}</div>
    
    <!-- 卡片的内容 -->
    <div class="mdui-card-content"><div id="test-editormd-view-{str(cnt)}" class="mdui-typo">
        <textarea style="display: none;" id="test-editormd-markdown-doc-{str(cnt)}">{i['answer']}</textarea>
      </div></div>
  
    <!-- 卡片的按钮 -->
    <div class="mdui-card-actions">
      <button class="mdui-btn mdui-ripple" onclick="likeit('{i['aid']}');">顶：{i['liked']}</button>
      <button class="mdui-btn mdui-btn-icon mdui-float-right">
        <i class="mdui-icon material-icons">expand_more</i>
      </button>
    </div>
  
  </div>
  <script>
       var md = document.getElementById("test-editormd-markdown-doc-{str(cnt)}").innerText;
        markdown_render_dom(document.getElementById("test-editormd-view-{str(cnt)}"), md);
    </script><br>'''
        print(escape(bb['question']))
        return readf('./static/temp.html').replace('<!-- title -->','文章').replace('<!-- documents -->',readf('./static/article_temp.html')).replace("<!-- problemkkk -->",pk).replace("(userid!!!)",email2usrid(bb['email'])).replace("avatar.jpg","/users_byid/"+email2usrid(bb['email'])+"/avatar.png").replace("<!-- asker -->",email2nickname(bb['email'])).replace("<!-- asker_oneword -->",get_oneword_byemail(bb['email'])).replace("<!-- title -->",bb['title']).replace("<!-- time -->",time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(bb['time']))).replace("<!-- the_same -->",str(bb['the_same'])).replace("<!-- question -->",escape(bb['question'])).replace("<!-- answers -->",t)

@app.route('/chat/<chat_id>')
def chat(chat_id):
    if(chat_id=='list'):
        username=get_username(session.get("logincookie"))
        if(username==None):
            return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
        li=get_chat_list()
        li = sort_humanly(li)
        li.reverse()
        print(li)
        t=''
        cnt=0
        for i in li:
            cnt+=1
            if(cnt>=23):
                break
            bb=json.loads(readf('./chat/benben/'+i))
            user=bb['user']
            if(not is_following(username,user)):
                if(username!=user):
                    continue
            info=bb['info']
            if(len(info)>300):
                info=info[:301]+'……'
            timee=bb['time']
            liked=bb['liked']
            reply=len(bb['reply'])
            rebenben=bb['rebenben']
            t+='''<br><div class="mdui-card mdui-hoverable">
            <!-- 卡片头部，包含头像、标题、副标题 -->
            <div class="mdui-card-header">
            <a href="/user/{}">
                        <img class="mdui-card-header-avatar" src="{}" />
                        <div class="mdui-card-header-title">
                            {}
                        </div>
                        <div class="mdui-card-header-subtitle">{}</div></a>
            </div>
            <div class="mdui-card-content" style="cursor:pointer" onclick="location.href='/chat/{}'">
                <div id="test-editormd-view-{}" class="mdui-typo" style="cursor:pointer">
                <textarea style="display:none;" id="test-editormd-markdown-doc-{}" style="cursor:pointer">{}</textarea>
            </div>
            </div>
            <div class="mdui-card-actions mdui-row-xs-5">
            <div class="mdui-col">
            <button class="mdui-btn mdui-btn-icon mdui-ripple" onclick="reply({});" mdui-tooltip="{{content: '回复', delay: 500}}">
                <i class="mdui-icon material-icons">chat_bubble_outline</i>
            </button>
            {}
            </div>
            <div class="mdui-col">
            <button class="mdui-btn mdui-btn-icon mdui-ripple" onclick="like({});" mdui-tooltip="{{content: '臆！好！', delay: 500}}">
                <i class="mdui-icon material-icons">exposure_plus_1</i>
            </button>
            {}
            </div>
            <div class="mdui-col">
            <button class="mdui-btn mdui-btn-icon mdui-ripple" onclick="kkzb({});" mdui-tooltip="{{content: '转犇', delay: 500}}">
                <i class="mdui-icon material-icons">repeat</i>
            </button>
            {}
            </div>
        </div>
        </div><script>
            $(function() {{
                var md = document.getElementById("test-editormd-markdown-doc-{}").innerText;
                markdown_render_dom(document.getElementById("test-editormd-view-{}"), md);
            }});
    </script>'''.format(email2usrid(user),"/users_byid/"+email2usrid(user)+"/avatar.png",email2nickname(user),json.loads(readf('./users/'+email2usrid(user)+'/profile.json'))['oneword'],str(i[:-5]),str(cnt),str(cnt),info,str(i[:-5]),str(reply),str(i[:-5]),str(liked),str(i[:-5]),str(rebenben),str(cnt),str(cnt),str(cnt),str(cnt))
        return readf('./static/temp.html').replace('<!-- title -->','犇犇').replace('<!-- documents -->',readf('./static/chat_list.html')).replace("<!-- lists -->",t).replace("avatar.jpg","/users/"+username+"/avatar.png").replace("<!-- username -->",username).replace("<!-- kk -->",t)
    else:
        username=get_username(session.get("logincookie"))
        if(username==None):
            return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
        if(not os.path.exists('./chat/benben/'+chat_id+'.json')):
            return abort(404)
        bb=json.loads(readf('./chat/benben/'+chat_id+'.json'))
        user=bb['user']
        info=bb['info']
        timee=bb['time']
        liked=bb['liked']
        reply=len(bb['reply'])
        rebenben=bb['rebenben']
        li=bb['reply']
        li = sort_humanly(li)
        li.reverse()
        t=''
        cnt=0
        for i in li:
            cnt+=1
            bb2=json.loads(readf('./chat/benben/'+str(i)+'.json'))
            user2=bb2['user']
            info2=bb2['info']
            if(len(info2)>100):
                info2=info2[:101]+'……'
            timee2=bb2['time']
            liked2=bb2['liked']
            reply2=len(bb2['reply'])
            rebenben2=bb2['rebenben']
            t+='''<div class="mdui-card mdui-hoverable"><div class="mdui-card-header">
            <a href="/user/{}">
                        <img class="mdui-card-header-avatar" src="{}" />
                        <div class="mdui-card-header-title">
                            {}
                        </div>
                        <div class="mdui-card-header-subtitle">{}</div></a>
            </div>
            <div class="mdui-card-content" style="cursor:pointer" onclick="location.href='/chat/{}'">
                <div id="test-editormd-view-{}" class="blog-single-desc" style="cursor:pointer">
                <textarea style="display:none;" id="test-editormd-markdown-doc-{}" style="cursor:pointer">{}</textarea>
            </div>
            </div>
            <div class="mdui-card-actions mdui-row-xs-5">
            <div class="mdui-col">
            <button class="mdui-btn mdui-btn-icon mdui-ripple" onclick="reply({});" mdui-tooltip="{{content: '回复', delay: 500}}">
                <i class="mdui-icon material-icons">chat_bubble_outline</i>
            </button>
            {}
            </div>
            <div class="mdui-col">
            <button class="mdui-btn mdui-btn-icon mdui-ripple" onclick="like({});" mdui-tooltip="{{content: '臆！好！', delay: 500}}">
                <i class="mdui-icon material-icons">exposure_plus_1</i>
            </button>
            {}
            </div>
            <div class="mdui-col">
            <button class="mdui-btn mdui-btn-icon mdui-ripple" onclick="kkzb({});" mdui-tooltip="{{content: '转犇', delay: 500}}">
                <i class="mdui-icon material-icons">repeat</i>
            </button>
            {}
            </div>
        </div>
        </div><script>
            $(function() {{
                var md=document.getElementById("test-editormd-markdown-doc-{}").innerText;
                markdown_render_dom(document.getElementById("test-editormd-view-{}"), md);
            }});//format里有，别删（document.getElementById("test-editormd-view-{}").classList.add("mdui-text-color-theme-text");
        </script><br>'''.format(email2nickname(user2),"/users_byid/"+email2usrid(user2)+"/avatar.png",email2nickname(user2),json.loads(readf('./users/'+email2usrid(user2)+'/profile.json'))['oneword'],str(i),str(cnt),str(cnt),info2,str(i),str(reply2),str(i),str(liked2),str(i),str(rebenben2),str(cnt),str(cnt),str(cnt))
        return readf('./static/temp.html').replace('<!-- title -->','犇犇').replace('<!-- documents -->',readf('./static/chat_temp.html')).replace("avatar.jpg","/users_byid/"+email2usrid(user)+"/avatar.png").replace("<!-- user -->",email2nickname(user)).replace("<!-- oneword -->",json.loads(readf('./users/'+email2usrid(user)+'/profile.json'))['oneword']).replace("<!-- time -->",time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timee))).replace("<!-- info -->",info).replace("<!-- reply -->",str(reply)).replace("<!-- like -->",str(liked)).replace("<!-- rebenben -->",str(rebenben)).replace("<!-- lists -->",t)

@app.route('/benben/reply',methods=['POST'])
def benben_reply():
    username=get_username(session.get("logincookie"))
    if(username==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
    if(get_activity_delta(username)<=5):
        return jsonify({'status':'too_fast'})
    record_activity(username)
    kk=new_benben(username=username,md=request.get_json()['msg'])
    add_reply(username,request.get_json()['benbenid'],kk)
    uid=get_profile(session.get("logincookie"))["userid"]
    msg={"user":email2nickname(username),"msg":f'<a href="/user/{uid}">{email2nickname(username)}</a> 回复了你的犇犇>>'}
    send_notice(email2usrid(get_benben_user(request.get_json()['benbenid'])),"犇犇回复",time.time(),json.dumps(msg),"/chat/"+str(request.get_json()['benbenid']))
    return json.dumps({"status":"success"})

@app.route('/benben/rebenben',methods=['POST'])
def benben_rebenben():
    username=get_username(session.get("logincookie"))
    if(username==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
    if(get_activity_delta(username)<=5):
        return jsonify({'status':'too_fast'})
    record_activity(username)
    rebenben_benben(username=username,benbenid=request.get_json()['benbenid'])
    uid=get_profile(session.get("logincookie"))["userid"]
    msg={"user":email2nickname(username),"msg":f'<a href="/user/{uid}">{email2nickname(username)}</a> 转发了你的犇犇>>'}
    send_notice(email2usrid(get_benben_user(request.get_json()['benbenid'])),"转犇",time.time(),json.dumps(msg),"/chat/"+str(request.get_json()['benbenid']))
    return json.dumps({"status":"success"})

@app.route('/benben/like',methods=['POST'])
def benben_like():
    username=get_username(session.get("logincookie"))
    if(username==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。")
    if(get_activity_delta(username)<=5):
        return jsonify({'status':'too_fast'})
    record_activity(username)
    if(username in json.loads(readf('./chat/benben/{}.json'.format(str(request.get_json()['benbenid']))))['who_liked']):
        return json.dumps({"status":"failed_already_liked"})
    like_benben(username=username,benbenid=request.get_json()['benbenid'])
    uid=get_profile(session.get("logincookie"))["userid"]
    msg={"user":email2nickname(username),"msg":f'<a href="/user/{uid}">{email2nickname(username)}</a> 赞了你的犇犇>>'}
    send_notice(email2usrid(get_benben_user(str(request.get_json()['benbenid']))),"犇犇点赞",time.time(),json.dumps(msg),"/chat/"+str(request.get_json()['benbenid']))
    return json.dumps({"status":"success"})

@app.route('/upload', methods =['POST'])
def upload():
    username=get_username(session.get("logincookie"))
    if(username==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。"), 403
    if(get_activity_delta(username)<=5):
        return jsonify({'status':'too_fast'})
    record_activity(username)
    file =  request.files.get('editormd-image-file')
    if not file:
        res = {
            'success' : 0,
            'message' : '上传失败'
        }
    else:
        ex = os.path.splitext(file.filename)[1]
        print(ex)
        filename = dt.datetime.now().strftime('%Y%m%d%H%M%S') + ex
        filename.replace("temp_","")
        print(filename)
        file.save(f'static//upload//%s' % filename)
        real_compress(filename)
        res = {
            'success' : 1,
            'message' : '上传成功',
            'url' : url_for('image', name = filename)
        }
    return jsonify(res)

@app.route('/image/<name>')
def image(name):
    with open(os.path.join('static//upload', name), 'rb') as f:
        resp = Response(f.read(), mimetype="image/jpeg")
    return resp

@app.route('/judgements/<task_id>')
def judgements(task_id):
    if(task_id)=='list':
        page=request.args.get("page")
        if(page==None):
            page=1
        page=int(page)
        li=get_judgement_list()
        li = sort_humanly(li)
        li.reverse()
        t=''
        cnt=0
        for i in li:
            cnt+=1
            if(cnt>page*10):
                break
            if(cnt<=(page-1)*10):
                continue
            kk=json.loads(readf("./judgements/"+i))
            kk['username']=email2nickname(kk['username'])
            if(kk['status'] in ['Compliling','Waiting','Judging']):
                t+='''<tr onclick="window.location='/judgements/{}'" style="cursor:pointer;"><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'''.format(i[:-5],kk['status'],i[:-5],kk['problem_id'],kk['language'],kk['username'])
            else:
                t+='''<tr onclick="window.location='/judgements/{}'" style="cursor:pointer;"><td><div class="mdui-chip mdui-color-{}"><span class="mdui-chip-title">{}</span></div></td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'''.format(i[:-5],COLOR(kk['status']),kk['status'],i[:-5],str(kk['problem_id']),kk['language'],kk['username'])
        return readf('./static/temp.html').replace('<!-- title -->','状态').replace('<!-- documents -->',readf('./static/judgements_list.html')).replace("<!-- lists -->",t)
    else:
        username=get_username(session.get('logincookie'))
        j=get_judgement(str(task_id))
        if(j['status']=='file_not_found'):
            return abort(404)
        else:
            j=j['info']
            if(username!=j['username'] and not is_admin_cookie(session.get('logincookie'))):
                return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html'))
            if(j['status']=='Compliling'):
                return readf('./static/temp.html')\
                .replace('<!-- documents -->',readf('./static/judgement_temp.html'))\
                .replace('<!-- problem_id -->',"Judging").replace('<!-- title -->','状态')\
                .replace("<!-- lang -->",j["language"])
            else:
                if(j['status'] == 'Compile Error'):
                    temp='''<div class="mdui-typo mdui-text-color-theme-text"><pre class="mdui-text-color-theme-text">{}</pre></div>'''.format(j['msg'])
                    return readf('./static/temp.html')\
                    .replace('<!-- documents -->',readf('./static/judgement_temp.html'))\
                    .replace('<!-- problem_id -->',"P"+str(j['problem_id']))\
                    .replace('<!-- title -->','状态')\
                    .replace('(code)',html.escape(j['code']))\
                    .replace('<!-- author -->',email2nickname(j['username'])).replace('<!-- judge_id -->',str(task_id)).replace('<!-- status -->',j['status']).replace('<!-- score -->',str(0)).replace('<!-- list -->',temp)\
                    .replace("<!-- lang -->",j["language"])
                elif(j['status'] not in ['Accepted','Wrong Answer','Partial Accepted']):
                    return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/judgement_temp.html')).replace('<!-- problem_id -->',"P"+str(j['problem_id'])).replace('<!-- title -->','状态').replace('(code)',html.escape(j['code'])).replace('<!-- author -->',email2nickname(j['username'])).replace('<!-- judge_id -->',str(task_id)).replace('<!-- realstatus -->',j['status'])\
                        .replace("<!-- lang -->",j["language"])
                else:
                    t=j['testpoints']
                    temp=''
                    cnt=0
                    for i in t:
                        cnt+=1
                        temp+=f'''<tr><td>{cnt}</td><td><div class="mdui-chip mdui-color-{COLOR(i['status'])}"><span class="mdui-chip-title">{i['status']}</span></div></td><td>{(i['time']/1000000):.2f}ms</td><td>{(i['memory']/(1024*1024)):.2f}MB</td></tr>'''
                    return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/judgement_temp.html')).replace('<!-- problem_id -->',"P"+str(j['problem_id'])).replace('<!-- title -->','状态').replace('(code)',html.escape(j['code'])).replace('<!-- author -->',email2nickname(j['username'])).replace('<!-- judge_id -->',str(task_id)).replace('<!-- status -->','''<div class="mdui-chip mdui-color-{}"><span class="mdui-chip-title">{}</span></div>'''.format(COLOR(j['status']),j['status'])).replace('<!-- score -->',str(j['score'])).replace('<!-- list -->',temp)\
                        .replace("<!-- lang -->",j["language"])

@app.route('/submit',methods=['POST'])
def submit():
    username=get_username(session.get('logincookie'))
    if(username!=None):
        if(get_activity_delta(username)<=5):
            return jsonify({'status':'too_fast'})
        record_activity(username)
        form=request.get_json()
        if(len(form['code'])==0):
            return {'status':'empty'}
        task_id=time.time()
        _thread.start_new_thread(throw_to_judge,(task_id,form,username,))
        return {"status":"Submit Accepted","task_id":task_id}
    else:
        return {"status":"Submit Failed","msg":"please_login_first"}

@app.route('/get_ide_result/<rid>')
def get_ide_result(rid):
    usermail=get_username(session.get("logincookie"))
    if(usermail==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。"), 403
    try:
        return readf("./ide_run_result/"+str(rid)+".json")
    except:
        return json.dumps({"status":"running"})

@app.route('/ide_submit',methods=['POST'])
def ide_submit():
    username=get_username(session.get('logincookie'))
    if(username!=None):
        form=request.get_json()
        task_id=time.time()
        _thread.start_new_thread(ide_throw_to_judge,(task_id,form,username,))
        return {"status":"Submit Accepted","task_id":task_id}
    else:
        return {"status":"Submit Failed","msg":"please_login_first"}

@app.route('/ace/src-noconflict/<file_name>')
def ace_src(file_name):
    return readf('./ace-builds-master/src-noconflict/'+file_name)

@app.route('/ace/src-noconflict/snippets/<file_name>')
def ace_src_sni(file_name):
    return readf('./ace-builds-master/src-noconflict/snippets/'+file_name)

@app.route('/problem/<problem_id>')
def problem(problem_id):
    if(problem_id)=='list':
        page=request.args.get("page")
        if(page==None):
            page=1
        page=int(page)
        li=get_problem_list()
        li=sort_humanly(li)
        t=''
        cnt=0
        usermail=get_username(session.get("logincookie"))
        for i in li:
            cnt+=1
            if(cnt>page*50):
                break
            if(cnt<=(page-1)*50):
                continue
            kk=get_problem(int(i))
            if(kk['type']=='contest'):
                kk['title']="<i>"+kk['title']+"(比赛赛题)</i>"
            if(kk['type']=='disabled'):
                kk['title']="<del>"+kk['title']+"(不可用)</del>"
            status={"passed":"✅","tried":"❌","none":" - "}
            t+='''<tr onclick="window.open('/problem/{}')" style="cursor:pointer;">
            <td>{}</td><td>{}</td><td>{}</td>
            <td><span class="tagchip mdui-text-truncate mdui-color-grey-800">{}</span></td>
            <td>{}</td></tr>'''.format(i,status[passed_problem(usermail,i)],i,kk['title'],merge_tag(kk['tags']),ac_rate(i))
        taglist=get_problem_tags()
        taghtml=''
        for i in taglist:
            if(len(i)<=10):
                taghtml+=f'''<a href="/search?q=tag%3A{i}#problem">{i}</a>&nbsp;&nbsp;&nbsp;'''
        return readf('./static/temp.html').replace('<!-- title -->','题库').replace('<!-- documents -->',readf('./static/problem_list.html')).replace("<!-- tags -->",taghtml).replace('<!-- lists -->',t)
    else:
        tr=request.args.get("translate")
        usermail=get_username(session.get("logincookie"))
        usernamee=email2nickname(usermail)
        p=get_problem(int(problem_id))
        shtml=''
        if(p['type']=='contest' or p['type']=='disabled'):
            if(not is_admin_cookie(session.get('logincookie'))):
                return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html'))
        cnt=0
        for i in p['samples']:
            cnt+=1
            shtml+='''<div class="container"><div class="input"><h2 class="mdui-text-color-theme">样例输入{}<button class="mdui-btn mdui-btn-icon mdui-ripple" onclick="copy(`{}`);"><i class="mdui-icon material-icons">content_copy</i></button></h2><pre class="mdui-text-color-theme-text">{}</pre></div><div class="output"><h2 class="mdui-text-color-theme">样例输出{}<button class="mdui-btn mdui-btn-icon mdui-ripple" onclick="copy(`{}`);"><i class="mdui-icon material-icons">content_copy</i></button></h2><pre class="mdui-text-color-theme-text">{}</pre></div></div>'''.format(str(cnt),raw_string(i['input']),i['input'],str(cnt),raw_string(i['output']),i['output'])
        shtml+='<br>'
        # 这么做是为了不显示value为0的数据，因为不这样做会有一根线段指向不知道什么东西很有误导性
        status=[i for i in json.loads(readf('problemset/'+str(problem_id)+'/status.json')) if i["value"]>0]
        if(tr==None):
            return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/problem_temp.html'))\
                .replace("(username)",str(usernamee))\
                .replace('<!-- title -->',escape(p['title']))\
                .replace('(problem_id)',escape(str(problem_id)))\
                .replace('<!-- problem_id -->',escape(str(problem_id)))\
                .replace('<!-- description -->',escape(p['description']['value']))\
                .replace('<!-- input -->',escape(p['input_description']['value']))\
                .replace('<!-- output -->',escape(p['output_description']['value']))\
                .replace('<!-- time_limit -->',str(p['time_limit']))\
                .replace('<!-- tips -->',escape(p['hint']['value']))\
                .replace('<!-- memory_limit -->',str(p['memory_limit']))\
                .replace('<!-- samples -->',shtml).replace('(data)',str(status))
        # else:
        #     return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/problem_temp.html'))\
        #         .replace("(username)",str(usernamee))\
        #         .replace('<!-- title -->',escape(p['title']))\
        #         .replace('(problem_id)',escape(str(problem_id)))\
        #         .replace('<!-- problem_id -->',escape(str(problem_id)))\
        #         .replace('<!-- description -->',escape(translate(p['description']['value'])))\
        #         .replace('<!-- input -->',escape(translate(p['input_description']['value'])))\
        #         .replace('<!-- output -->',escape(translate(p['output_description']['value'])))\
        #         .replace('<!-- time_limit -->',str(p['time_limit']))\
        #         .replace('<!-- tips -->',escape(translate(p['hint']['value'])))\
        #         .replace('<!-- memory_limit -->',str(p['memory_limit']))\
        #         .replace('<!-- samples -->',shtml).replace('(data)',str(status))

@app.route('/contest/<contest_id>')
def contest(contest_id):
    if(contest_id)=='list':
        page=request.args.get("page")
        if(page==None):
            page=1
        page=int(page)
        li=get_contest_list()
        li=sort_humanly(li)
        li.reverse()
        t=''
        cnt=0
        for i in li:
            cnt+=1
            if(cnt>page*20):
                break
            if(cnt<=(page-1)*20):
                continue
            kk=json.loads(readf("./contest/"+i))
            if(kk['starttime']>time.time()):
                status="未开始"
            elif(kk['starttime']<=time.time() and kk['endtime']>time.time()):
                status="进行中"
            else:
                status="已结束"
            t+=f'''<tr onclick="window.location='/contest/{i[:-5]}'" style="cursor:pointer;">
            <td>{status}</td><td>{i[:-5]}</td><td>{kk['name']}</td>
            <td><span class="tagchip mdui-text-truncate mdui-color-grey-800">{merge_tag(kk['tags'])}</span></td>
            <td>{time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(float(kk['starttime'])))} ~ {time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(float(kk['endtime'])))}</td>
            <td>{len(kk['problemlist'])}</td></tr>'''
        return readf('./static/temp.html').replace('<!-- title -->','比赛').replace('<!-- documents -->',readf('./static/contest_list.html')).replace('<!-- lists -->',t)
    else:
        usermail=get_username(session.get("logincookie"))
        if(usermail==None):
            return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。"), 403
        p=json.loads(readf("./contest/"+contest_id+".json"))
        if(p['starttime']>time.time()):
            if(not is_taking_part_in(contest_id,usermail)):
                return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/contest_temp.html')).replace('<!-- name -->',p['name']).replace('<!-- title -->',p['name']).replace("<!-- subname -->",time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(float(p['starttime'])))+" ~ "+time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(float(p['endtime'])))+" <b>未开始</b>").replace("<!-- info -->",escape(p['description'])).replace("<!-- list -->","<center><h4>未开始 且 未参加 试题保密</h4></center>")
            else:
                return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/contest_temp.html')).replace('<!-- name -->',p['name']).replace('<!-- title -->',p['name']).replace("<!-- subname -->",time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(float(p['starttime'])))+" ~ "+time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(float(p['endtime'])))+" <b>未开始</b>").replace("<!-- info -->",escape(p['description'])).replace("<!-- list -->","<center><h4>比赛未开始 试题保密</h4></center>")
        if(p['endtime']<time.time()):
            problemlisthtml=''
            prokkk=''
            cnt=0
            num2let=['','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
            for i in p['problemlist']:
                cnt+=1
                problemlisthtml+=f'''<tr onclick="window.location='/problem/{i}'" style="cursor:pointer;">
                    <td>{num2let[cnt]}</td>
                    <td>{str(get_full_score(str(i)))}</td>
                    <td>{get_problem(str(i))['title']}</td><td></td></tr>'''
                prokkk+=f'''<th>{str(num2let[cnt])}</th>'''
            res=sorted(p['rank'].items(),key=lambda s:(total_score(s),total_try(s)))
            res.reverse()
            rankhtml=''
            cnt=0
            for i in res:
                cnt+=1
                k=''
                for j in p['problemlist']:
                    k+=f'''<td>{str(i[1][j]['score'])} (-{str(i[1][j]['tried_times'])})</td>'''
                rankhtml+=f'''<tr>
                    <td>#{str(cnt)}</td>
                    <td>{email2nickname(i[0])}</td>
                    <td>{total_score(i)}</td>
                    {k}</tr>'''
            return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/contest_temp.html')).replace('<!-- name -->',p['name']).replace('<!-- title -->',p['name']).replace('''<button class="mdui-btn mdui-color-theme-accent mdui-ripple mdui-float-right" onclick="enter();">报名</button>''','').replace("<!-- subname -->",time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(float(p['starttime'])))+" ~ "+time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(float(p['endtime'])))+" <b>已结束</b>").replace("<!-- info -->",escape(p['description'])).replace("<!-- list -->","<center><h4>竞赛已结束</h4></center>").replace("<!-- problemskkk -->",prokkk).replace("报名","已报名").replace('onclick="enter();"','disabled').replace('<!-- title -->',p['name']).replace("<!-- rank -->",rankhtml).replace('<!-- name -->',p['name']).replace('<!-- subname -->',time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(float(p['starttime'])))+" ~ "+time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(float(p['endtime'])))+" <b>进行中</b>").replace("<!-- info -->",escape(p['description'])).replace("<!-- list -->",problemlisthtml)
        if(not is_taking_part_in(contest_id,usermail)):
            return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/contest_temp.html')).replace('<!-- name -->',p['name']).replace('<!-- title -->',p['name']).replace("<!-- subname -->",time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(float(p['starttime'])))+" ~ "+time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(float(p['endtime'])))+" <b>未开始</b>").replace("<!-- info -->",escape(p['description'])).replace("<!-- list -->","<center><h4>已开始 但 未参加 试题保密</h4></center>")
        problemlisthtml=''
        prokkk=''
        cnt=0
        num2let=['','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
        for i in p['problemlist']:
            cnt+=1
            problemlisthtml+=f'''<tr onclick="window.location='/contest/{contest_id}/problem/{num2let[cnt]}'" style="cursor:pointer;">
                  <td>{num2let[cnt]}</td>
                  <td>{str(get_full_score(str(i)))}</td>
                  <td>{get_problem(str(i))['title']}</td><td></td></tr>'''
            prokkk+=f'''<th>{str(num2let[cnt])}</th>'''
        res=sorted(p['rank'].items(),key=lambda s:(total_score(s),total_try(s)))
        res.reverse()
        rankhtml=''
        cnt=0
        for i in res:
            cnt+=1
            k=''
            for j in p['problemlist']:
                k+=f'''<td>{str(i[1][j]['score'])} (-{str(i[1][j]['tried_times'])})</td>'''
            rankhtml+=f'''<tr>
                  <td>#{str(cnt)}</td>
                  <td>{email2nickname(i[0])}</td>
                  <td>{total_score(i)}</td>
                  {k}</tr>'''
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/contest_temp.html')).replace("<!-- problemskkk -->",prokkk).replace("报名","已报名").replace('onclick="enter();"','disabled').replace('<!-- title -->',p['name']).replace("<!-- rank -->",rankhtml).replace('<!-- name -->',p['name']).replace('<!-- subname -->',time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(float(p['starttime'])))+" ~ "+time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(float(p['endtime'])))+" <b>进行中</b>").replace("<!-- info -->",escape(p['description'])).replace("<!-- list -->",problemlisthtml)

@app.route('/contest/<cid>/problem/<pcode>')
def contest_problem(cid,pcode):
    contest_id=cid
    num2let=['','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
    pid=0
    for i in range(1,len(num2let)+1):
        if(num2let[i]==pcode):
            pid=i-1
            break
    usermail=get_username(session.get("logincookie"))
    if(usermail==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。"), 403
    p=json.loads(readf("./contest/"+contest_id+".json"))
    problem_id=p['problemlist'][pid]
    if(p['starttime']>time.time()):
        if(not is_taking_part_in(contest_id,usermail)):
            return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/contest_problem_temp.html')).replace('''<!--kk-->''','''<script>mdui.snackbar("比赛未开始且您未报名");</script>''')
        else:
            return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/contest_problem_temp.html')).replace('''<!--kk-->''','''<script>mdui.snackbar("比赛未开始");</script>''')
    if(p['endtime']<time.time()):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/contest_problem_temp.html')).replace('''<!--kk-->''','''<script>mdui.snackbar("比赛已结束");</script>''')
    if(not is_taking_part_in(contest_id,usermail)):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/contest_problem_temp.html')).replace('''<!--kk-->''','''<script>mdui.snackbar("比赛正在进行中，您还未报名！");</script>''')
    p=get_problem(int(problem_id))
    shtml=''
    cnt=0
    for i in p['samples']:
        cnt+=1
        shtml+='''<div class="container"><div class="input"><h2 class="mdui-text-color-theme">样例输入{}<button class="mdui-btn mdui-btn-icon mdui-ripple" onclick="copy(`{}`);"><i class="mdui-icon material-icons">content_copy</i></button></h2><pre class="mdui-text-color-theme-text">{}</pre></div><div class="output"><h2 class="mdui-text-color-theme">样例输出{}<button class="mdui-btn mdui-btn-icon mdui-ripple" onclick="copy(`{}`);"><i class="mdui-icon material-icons">content_copy</i></button></h2><pre class="mdui-text-color-theme-text">{}</pre></div></div>'''.format(str(cnt),raw_string(i['input']),i['input'],str(cnt),raw_string(i['output']),i['output'])
    shtml+='<br>'
    # 这么做是为了不显示value为0的数据，因为不这样做会有一根线段指向不知道什么东西很有误导性
    status=[i for i in json.loads(readf('problemset/'+str(problem_id)+'/status.json')) if i["value"]>0]
    return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/contest_problem_temp.html')).replace("(contest_id)",str(cid)).replace("(problem_id)",str(problem_id)).replace("(contest_id)",str(contest_id)).replace('<!-- title -->',escape(p['title'])).replace('(problem_id)',escape(str(problem_id))).replace('<!-- problem_id -->',escape(str(problem_id))).replace('<!-- description -->',escape(p['description']['value'])).replace('<!-- input -->',escape(p['input_description']['value'])).replace('<!-- output -->',escape(p['output_description']['value'])).replace('<!-- time_limit -->',str(p['time_limit'])).replace('<!-- tips -->',escape(p['hint']['value'])).replace('<!-- memory_limit -->',str(p['memory_limit'])).replace('<!-- samples -->',shtml).replace('(data)',str(status))

@app.route('/contest_submit',methods=['POST'])
def contest_submit():
    username=get_username(session.get('logincookie'))
    if(username!=None):
        form=request.get_json()
        task_id=time.time()
        _thread.start_new_thread(throw_to_judge_contest,(task_id,form,username,))
        return {"status":"Submit Accepted","task_id":task_id}
    else:
        return {"status":"Submit Failed","msg":"please_login_first"}

@app.route('/enter/<cid>')
def enter(cid):
    usermail=get_username(session.get("logincookie"))
    if(usermail==None):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。"), 403
    j=json.loads(readf(f"./contest/{cid}.json"))
    if(usermail in j['participants']):
        return json.dumps({"status":"failed"})
    j['participants'].append(usermail)
    temp={}
    for i in j['problemlist']:
        temp[i]={"tried_times":0,"score":0}
    j['rank'][usermail]=temp
    savef(f"./contest/{cid}.json",json.dumps(j))
    return json.dumps({"status":"succeed"})

@app.route('/code')
def get_code():
    image, str = validate_picture()
    # 将验证码图片以二进制形式写入在内存中，防止将图片都放在文件夹中，占用大量磁盘
    buf = BytesIO()
    image.save(buf, 'jpeg')
    buf_str = buf.getvalue()
    # 把二进制作为response发回前端，并设置首部字段
    response = make_response(buf_str)
    response.headers['Content-Type'] = 'image/gif'
    # 将验证码字符串储存在session中
    session['image'] = str
    return response
@app.route("/user_byname/<name>")
def user_byname(name):
    name=str(name)
    if(not user_exist(name)):
        return abort(404)
    else:
        email=nick_to_email(name)
        uid=email2usrid(email)
        return safe_redirect(f"/user/{uid}")
@app.route('/user/<userid>')
def user(userid):
    email=userid2email(userid)
    if(os.path.exists('./users/'+email2usrid(email))):
        userdat=json.loads(readf('./users/userandpass.json'))[email]
        wssb=''
        if(email!=get_username(session.get('logincookie'))):
            wssb='hidden=hidden'
        j=json.loads(readf('./users/'+email2usrid(email)+'/profile.json'))
        oneword=j['oneword']
        tj=json.loads(readf('./users/'+email2usrid(email)+'/train.json'))
        aced=""
        tried=""
        username=get_username(session.get("logincookie"))
        if(username==None):
            return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html')).replace("您无权查看此页面<br>即将返回上一页面","请先登录。"), 403
        realj="/follow/"
        realw="关注"
        if(is_following(username,userid2email(userid))):
            realj="/unfollow/"
            realw="取消关注"
        bandages=get_bandages_by_userdat(userdat,email)
        for i in tj['passed']:
            aced+='''<a href="/problem/{}">[{}]</a>&nbsp;&nbsp;&nbsp;'''.format(str(i),str(i))
        for i in tj['tried']:
            tried+='''<a href="/problem/{}">[{}]</a>&nbsp;&nbsp;&nbsp;'''.format(str(i),str(i))
        followershtml=''
        kk=json.loads(readf('./users/followed_list.json'))
        # print(kk)
        if(userid2email(userid) not in kk.keys()):
            kk[userid2email(userid)]=[]
        # print(kk)
        for i in kk[userid2email(userid)]:
            followershtml+=f'''<a href="/user/{str(email2usrid(i))}">{email2nickname(i)}</a>&nbsp;&nbsp;&nbsp;'''
        followingshtml=''
        kk=json.loads(readf('./users/follow_list.json'))
        if(userid2email(userid) not in kk.keys()):
            kk[userid2email(userid)]=[]
        for i in kk[userid2email(userid)]:
            followingshtml+=f'''<a href="/user/{str(email2usrid(i))}">{email2nickname(i)}</a>&nbsp;&nbsp;&nbsp;'''
        return readf('./static/temp.html').replace('<!-- title -->',
            email2nickname(email)+'的个人空间')\
                .replace('<!-- documents -->',readf('./static/user.html'))\
                .replace("<!-- followers -->",followershtml).replace("<!-- followings -->",followingshtml)\
                .replace('关注',realw)\
                .replace('<!-- introduction -->',(readf('./users/{}/introduction.md'.format(email2usrid(email)))))\
                .replace('/follow/',realj)\
                .replace('<!-- oneword -->',oneword)\
                .replace('<!-- username -->',email2nickname(email))\
                .replace('<!-- aced -->',aced).replace('<!-- tried -->',tried)\
                .replace('<!-- userid -->',email2usrid(email)).replace("我是傻逼",wssb)\
                .replace("<!-- bandages -->"," ".join(bandages))
    return abort(404)
@app.route('/users_byid/<username>/<filename>')
def userfile_byid(username,filename):
    if(os.path.exists('./users/'+username+'/'+filename)):
        with open('./users/'+username+'/'+filename, 'rb') as f:
            res = (f.read())
            return res

@app.route('/users/<username>/<filename>')
def userfile(username,filename):
    username=email2usrid(username)
    if(os.path.exists('./users/'+username+'/'+filename)):
        with open('./users/'+username+'/'+filename, 'rb') as f:
            res = (f.read())
            return res

@app.route('/get_profile')
def get_profile_ser():
    if(session.get('logincookie')==None):
        return json.dumps({'status':'failed','msg':'need_login'})
    elif(not cookie_valid(session.get('logincookie'))):
        return json.dumps({'status':'failed','msg':'cookie_isnt_valid'})
    else:
        return json.dumps({'status':'success','msg':get_profile(session.get('logincookie'))})

@app.route('/reallogout')
def reallogout():
    session.pop('logincookie',None)
    return json.dumps({'status':'success','msg':'ok'})

@app.route('/logout')
def logout():
    session.pop('logincookie',None)
    return '''<script>location.href='/#loggedout';</script>'''

@app.route('/login')
def login():
    try:
        return readf('./static/temp.html').replace('<!-- title -->','登录').replace('<!-- documents -->',readf('./static/login.html'))
    except:
        pass
    finally:
        D=json.loads(readf("./users/logincookie.json"))
        try:
            for key in (D.keys()):
                if float(D[key]['time'])<time.time():
                    del D[key]
                    continue
        except:
            pass
        finally:
            savef("./users/logincookie.json",json.dumps(D))

@app.route('/login_request',methods=['POST','GET'])
def lr():
    form=request.get_json()
    if(not verify_captcha(form['captcha'])):
        return json.dumps({'status':'failed','msg':'captcha_error'})
    elif(get_password(form['username'])==get_hash(form['password'])):
        lcookie=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(2333))
        session['logincookie']=lcookie
        session.permanent = True
        set_lcookie(lcookie,form['username'],time.time()+259200)
        return json.dumps({'status':'success','msg':'ok'})
    else:
        return json.dumps({'status':'failed','msg':'username_or_password_wrong'})

@app.route('/new_account_request',methods=['POST','GET'])
def nar():
    form=request.get_json()
    if(not verify_captcha(form['captcha'])):
        return json.dumps({'status':'failed','msg':'captcha_error'})
    elif(user_exist(form['username'])):
        return json.dumps({'status':'failed','msg':'username_already_exists'})
    elif(len(form['username'])>15):
        return json.dumps({'status':'failed','msg':'username_too_long'})
    elif(not is_valid_nickname(form['username'])):
        return json.dumps({'status':'failed','msg':'username_is_illegal'})
    elif(is_valid_email(form['mail'])==False):
        return json.dumps({'status':'failed','msg':'email_is_illegal'})
    elif(not parse_email_domain(form['mail']) in ['qq.com','163.com','foxmail.com','126.com','yeah.net']):
        return json.dumps({'status':'failed','msg':'email_domain_is_illegal'})
    elif(mail_exist(form['mail'])):
        return json.dumps({'status':'failed','msg':'mail_already_exists'})
    else:
        url=genRandomString(50)
        timee=time.time()+300
        waiting(form['username'],get_hash(form['password']),form['mail'],url,timee)
        realurl="https://oj.amzcd.top/checkout/"+url
        send_email(form['mail'],' - TasOJ - ','Please access the following link within 5 minutes in order to activate your account:{}'.format(realurl))
        return json.dumps({'status':'success','msg':'ok'})

@app.route('/checkout/<u>')
def checkout(u):
    j=json.loads(readf("./users/waiting.json"))
    if(u in j.keys()):
        ac=j[u]
        j.pop(u)
        savef('./users/waiting.json',json.dumps(j))
        if(time.time()<=ac['time']):
            userid=str(get_user_amount()+1)
            us=json.loads(readf("./users/userandpass.json"))
            # 由于发送请求时已经变成哈希了，这里不需要get_hash
            us[ac['email']]={'password':ac['password'],'username':ac['username'],"bandages":[]}
            savef('./users/userandpass.json',json.dumps(us))
            os.mkdir('./users/'+userid)
            kkk=json.loads(readf(('./users/e2u.json')))
            kkk[ac['email']]=userid
            savef('./users/e2u.json',json.dumps(kkk))
            codee='''<script>setTimeout(function() {mdui.dialog({
        title: '(title)',
        content: '(content)',
        buttons: [
            {
                text: '取消'
            },
            {
                text: '确认',
                onClick: function (inst) {
                    location.href = "/login"
                }
            }
        ]
    }); }, 500);</script>'''.replace('(title)','恭喜！注册成功！').replace('(content)','立即前往登录页面')
            create_new_account(userid)
            return readf('./static/temp.html').replace('<!-- title -->','注册').replace('<!-- documents -->',readf('./static/register_info.html')).replace("<!-- extra -->",codee)
        else:
            codee='''<script>setTimeout(function() {mdui.dialog({
        title: '(title)',
        content: '(content)',
        buttons: [
            {
                text: '取消'
            },
            {
                text: '确认',
                onClick: function (inst) {
                    location.href = "(href)"
                }
            }
        ]
    }); }, 500);</script>'''.replace('(title)','注册失败……该链接已失效').replace('(content)','请在5分钟内进入链接').replace('(href)','/register')
            return readf('./static/temp.html').replace('<!-- title -->','注册').replace('<!-- documents -->',readf('./static/register_info.html')).replace("<!-- extra -->",codee)
    else:
        codee='''<script>setTimeout(function() {mdui.dialog({
        title: `(title)`,
        content: `(content)`,
        buttons: [
            {
                text: '取消'
            },
            {
                text: '确认',
                onClick: function (inst) {
                    location.href = "(href)"
                }
            }
        ]
    }); }, 500);</script>'''.replace('(title)',"What's up!?!").replace('(content)','该链接无效').replace('(href)','/login')
        return readf('./static/temp.html').replace('<!-- title -->','注册').replace('<!-- documents -->',readf('./static/register_info.html')).replace("<!-- extra -->",codee)

@app.route('/register')
def register():
    return readf('./static/temp.html').replace('<!-- title -->','注册').replace('<!-- documents -->',readf('./static/register.html'))

@app.route('/')
def index():
    with open("./site/notice.md",encoding="utf-8")as fp:
        md=fp.read()
    md=md
    return readf('./static/temp.html').replace('<!-- title -->','首页').replace('<!-- documents -->',
    readf('./static/index.html').replace("<!-- notice -->",md))

@app.route('/study')
def study():
    li=get_study_list()
    li=sort_humanly(li)
    html=''
    for i in li:
        j=json.loads(readf("./study/"+i))
        html+=f'''<div class="mdui-row mdui-col-xs-6 mdui-col-sm-4 studycard">
                    <div class="mdui-card mdui-ripple" onclick="window.open('/study/{i[:-5]}');">
                    <div class="mdui-card-media">
                        <img src="{j['image']}" />
                        <div class="mdui-card-media-covered">
                        <div class="mdui-card-primary">
                            <div class="mdui-card-primary-title">{j['title']}</div>
                            <div class="mdui-card-primary-subtitle">{j['subtitle']}</div>
                        </div>
                        </div>
                    </div>
                    </div>
                </div>'''
    return readf('./static/temp.html').replace('<!-- title -->','学习').replace('<!-- documents -->',readf('./static/study.html')).replace("<!-- list -->",html)

@app.route('/study/<sid>')
def study_sid(sid):
    j=json.loads(readf("./study/"+str(sid)+".json"))
    listhtml=''
    cnt=0
    TYPES={"outerlink":"外链","article":"文章","problem":"题目"}
    for i in j['content']:
        cnt+=1
        shortlink=''
        if(len(i['link'])>50):
            shortlink=i['link'][:50]+'…'
        else:
            shortlink=i['link']
        listhtml+=f'''<tr>
                      <td>{str(cnt)}</td>
                      <td>{TYPES[i['type']]}</td>
                      <td>{i['title']}</td>
                      <td><a href="{i['link']}">{shortlink}</a></td>
                    </tr>'''
    return readf('./static/temp.html').replace('<!-- title -->','学习').replace('<!-- documents -->',readf('./static/study_temp.html'))\
        .replace("<!-- Title -->",j['title'])\
        .replace("<!-- Subtitle -->",j['subtitle'])\
        .replace("<!-- intro -->",j['introduction'])\
        .replace('<!-- list -->',listhtml)

@app.route('/ide')
def ide():
    return readf('./static/temp.html').replace('<!-- title -->','在线IDE').replace('<!-- documents -->',readf('./static/ide.html'))

@app.route('/buglist')
def buglist():
    return readf('./static/temp.html').replace('<!-- title -->','TasOJ Buglist').replace('<!-- documents -->',readf('./static/buglist.html'))

@app.route('/feedback')
def feedback():
    return readf('./static/temp.html').replace('<!-- title -->','反馈').replace('<!-- documents -->',readf('./static/feedback.html'))

@app.route('/about')
def about():
    return readf('./static/temp.html').replace('<!-- title -->','关于').replace('<!-- documents -->',readf('./static/about.html'))

@app.route('/admin/problemdel',methods=['POST'])
def admin_problemdel():
    if(not is_admin_cookie(session.get('logincookie'))):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html'))
    form=request.get_json()
    shutil.rmtree('./problemset/'+str(form['problemid']), ignore_errors=True)
    return json.dumps({"status":"success"})

@app.route('/admin/newproblem',methods=['POST'])
def admin_newproblem():
    if(not is_admin_cookie(session.get('logincookie'))):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html'))
    form=request.get_json()
    amount=int(get_last_pid())
    newpid=amount+1
    source_path = os.path.abspath(r'./problem_temp_sample')
    target_path = os.path.abspath(r'./problemset/'+str(newpid))
    if not os.path.exists(target_path):
        os.makedirs(target_path)
    if os.path.exists(source_path):
        shutil.rmtree(target_path)
    shutil.copytree(source_path, target_path)
    return json.dumps({"status":"success","pid":newpid})

@app.route('/admin/problemcopy',methods=['POST'])
def admin_problemcopy():
    if(not is_admin_cookie(session.get('logincookie'))):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html'))
    form=request.get_json()
    amount=int(get_last_pid())
    newpid=amount+1000
    source_path = os.path.abspath(r'./problemset/'+str(form['problemid']))
    target_path = os.path.abspath(r'./problemset/'+str(newpid))
    if not os.path.exists(target_path):
        os.makedirs(target_path)
    if os.path.exists(source_path):
        shutil.rmtree(target_path)
    shutil.copytree(source_path, target_path)
    return json.dumps({"status":"success","pid":newpid})

@app.route('/admin/dataset',methods=['POST'])
def admin_dataset():
    if(not is_admin_cookie(session.get('logincookie'))):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html'))
    form=request.get_json()
    p=json.loads(readf("./problemset/"+str(form['problemid'])+"/problem.json"))
    p['test_case_score']=[]
    for i in form['data']:
        p['test_case_score'].append({'score':int(i[1]),'input_name':i[0],'output_name':i[0][:i[0].rfind('.')]+'.out'})
    savef("./problemset/"+str(form['problemid'])+"/problem.json",json.dumps(p))
    return json.dumps({"status":"success"})

@app.route('/admin/problemupload',methods=['POST'])
def admin_problemupload():
    if(not is_admin_cookie(session.get('logincookie'))):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html'))
    form=request.get_json()
    p=json.loads(readf("./problemset/"+str(form['problemid'])+"/problem.json"))
    p['title']=form['title']
    p['description']['value']=form['description']
    p['input_description']['value']=form['input_description']
    p['output_description']['value']=form['output_description']
    p['hint']['value']=form['hint']
    p['type']=form['status']
    p['time_limit']=form['time_limit']
    p['tags']=form['tags']
    p['memory_limit']=form['memory_limit']
    cnt=0
    p['samples']=[]
    for i in form['samples']:
        cnt+=1
        # print(i)
        p['samples'].append({"input":i[0],"output":i[1]})
    savef("./problemset/"+str(form['problemid'])+"/problem.json",json.dumps(p))
    return json.dumps({"status":"success"})

@app.route("/admin/upload/<pid>",methods=['POST','GET'])
def admin_upload_pid(pid):
    if(not is_admin_cookie(session.get('logincookie'))):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html'))
    file = request.files['myfile']
    if file:
        fid=time.time()
        file.save(os.path.join("./zip", file.filename+str(fid)+".zip"))
        zip_ref = zipfile.ZipFile(os.path.join("./zip", file.filename+str(fid)+".zip"), 'r')
        zip_ref.extractall(os.path.join("./problemset", pid+"/testcase"))
        zip_ref.close()
        os.remove(os.path.join("./zip", file.filename+str(fid)+".zip"))
        p=json.loads(readf("./problemset/"+pid+"/problem.json"))
        li=get_data_list(pid)
        p['test_case_score']=[]
        li=sort_humanly(li)
        for i in li:
            if(i.split('.')[-1]=='out'):
                continue
            p['test_case_score'].append({'score':0,'input_name':i,'output_name':i[:i.rfind('.')]+'.out'})
        savef("./problemset/"+pid+"/problem.json",json.dumps(p))
        return "success"

@app.route("/admin/download/<pid>")
def admin_download_pid(pid):
    if(not is_admin_cookie(session.get('logincookie'))):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html'))
    #需要压缩的文件夹
    input_path = "./problemset/"+pid+"/testcase"
    #压缩后存放位置
    output_path = './zip'
    #压缩后的文件名
    output_name = "P"+pid+'_'+str(time.time())+'.zip'
    f = zipfile.ZipFile(output_path + '/' + output_name, 'w', zipfile.ZIP_DEFLATED)
    filelists = []
    files = os.listdir(input_path)
    for file in files:
        if os.path.isdir(input_path + '/' + file):
            filelists.append(input_path + '/' + filelists)
        else:
            filelists.append(input_path + '/' + file)

    for file in filelists:
        f.write(file)
    # 调用了close方法才会保证完成压缩
    f.close()
    # print(output_path + r"/" + output_name)
    return send_from_directory(output_path,output_name)

@app.route('/admin/problemedit/<problem_id>')
def admin_problemedit_pid(problem_id):
    if(not is_admin_cookie(session.get('logincookie'))):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html'))
    usermail=get_username(session.get("logincookie"))
    usernamee=email2nickname(usermail)
    p=get_problem(int(problem_id))
    datahtml=''
    cnt=0
    for i in p['test_case_score']:
        cnt+=1
        datahtml+=f'''<tr id="case_{str(cnt)}">
                    <td>{str(cnt)}</td>
                    <td>{i['input_name']}</td>
                    <td>
                        <button class="mdui-btn mdui-btn-icon mdui-ripple" disabled onclick="edittestcase({str(cnt)});">
                            <i class="mdui-icon material-icons" >edit</i>
                        </button>
                    </td>
                    <td>{i['output_name']}</td>
                    <td>
                        <button class="mdui-btn mdui-btn-icon mdui-ripple" disabled onclick="edittestcase({str(cnt)});">
                            <i class="mdui-icon material-icons" >edit</i>
                        </button>
                    </td>
                    <td>
                        <div class="mdui-textfield">
                            <input class="mdui-textfield-input" type="number" id="score-{str(cnt)}" placeholder="分值"/>
                            <script>document.getElementById("score-{str(cnt)}").value = {str(i['score'])}</script>
                        </div>
                    </td>
                </tr>'''
    shtml=''
    cnt=0
    for i in p['samples']:
        cnt+=1
        shtml+=f'''<tr id="sample_{str(cnt)}">
                    <td>{str(cnt)}</td>
                    <td>
                        <div class="mdui-textfield">
                            <textarea class="mdui-textfield-input" placeholder="样例输入">{i['input']}</textarea>
                        </div>
                    </td>
                    <td>
                        <div class="mdui-textfield">
                            <textarea class="mdui-textfield-input" placeholder="样例输出">{i['output']}</textarea>
                        </div>
                    </td>
                    <td>
                        <button class="mdui-btn mdui-btn-icon mdui-ripple" onclick="delsample({str(cnt)});">
                            <i class="mdui-icon material-icons">cancel</i>
                        </button>
                    </td>
                </tr>'''
    shtml+='<br>'
    taghtml=''
    taglist=p['tags']
    for i in taglist:
        taghtml+=f'''<div class="mdui-chip" id="chip-{i}">
                        <span class="mdui-chip-title">{i}</span>
                        <span class="mdui-chip-delete" onclick="document.getElementById('chip-{i}').remove();for (var key in window['tags']) {{ if (window['tags'][key] === `{i}`) {{ window['tags'].splice(key, 1) }} }}">
                            <i class="mdui-icon material-icons">cancel</i>
                        </span>
                    </div>'''
    check1=check2=check3=""
    if(p['type']=='disabled'):
        check1='checked="checked"'
    elif(p['type']=='problem'):
        check2='checked="checked"'
    elif(p['type']=='contest'):
        check3='checked="checked"'
    # 这么做是为了不显示value为0的数据，因为不这样做会有一根线段指向不知道什么东西很有误导性
    status=[i for i in json.loads(readf('problemset/'+str(problem_id)+'/status.json')) if i["value"]>0]
    return readf('./static/admin_temp.html').replace('<!-- documents -->',readf('./static/problem_edit_temp.html')).replace("<!-- data table -->",datahtml).replace("(tagsss)",str(taglist)).replace("(problem_id)",str(problem_id)).replace("(username)",usernamee).replace("不可用check",check1).replace("公众可见check",check2).replace("比赛赛题check",check3).replace("<!-- taglist -->",taghtml).replace('<!-- title -->',escape(p['title'])).replace('(problem_id)',escape(str(problem_id))).replace('<!-- problem_id -->',escape(str(problem_id))).replace('<!-- description -->',escape(p['description']['value'])).replace('<!-- input -->',escape(p['input_description']['value'])).replace('<!-- output -->',escape(p['output_description']['value'])).replace('<!-- time_limit -->',str(p['time_limit'])).replace('<!-- tips -->',escape(p['hint']['value'])).replace('<!-- memory_limit -->',str(p['memory_limit'])).replace('<!-- samplelists -->',shtml).replace('(data)',str(status))

@app.route('/admin/studyedit/<sid>')
def admin_studyedit_sid(sid):
    if(not is_admin_cookie(session.get('logincookie'))):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html'))
    j=(readf("./study/"+str(sid)+".json"))
    return readf('./static/admin_temp.html').replace('<!-- title -->','学习编辑').replace('<!-- documents -->',readf('./static/study_edit_temp.html')).replace("<!-- json -->",j).replace("(sid)",str(sid))

@app.route('/admin/save_study_edit/<sid>',methods=['POST'])
def admin_save_study_edit(sid):
    if(not is_admin_cookie(session.get('logincookie'))):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html'))
    savef("./study/"+str(sid)+".json",request.get_json()['code'])
    return "succeed"

@app.route('/admin/newstudy',methods=['POST'])
def admin_newstudy():
    if(not is_admin_cookie(session.get('logincookie'))):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html'))
    amount=int(get_last_sid()[:-5])
    newpid=amount+1
    savef("./study/"+str(newpid)+".json",'''{
    "title":"这是标题",
    "subtitle":"副标题",
    "image":"封面图片【链接】",
    "introduction":"介绍",
    "content":[
        {"type":"outerlink","title":"什么是OI","link":"https://baike.baidu.com"},
        {"type":"article","title":"一切的基石","link":"/article/4"},
        {"type":"problem","title":"A+B实战演练","link":"/problem/1000"}
    ]
}''')
    return json.dumps({"status":"success","pid":newpid})

@app.route('/admin/studyedit')
def admin_studyedit():
    if(not is_admin_cookie(session.get('logincookie'))):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html'))
    page=request.args.get("page")
    if(page==None):
        page=1
    page=int(page)
    li=get_study_list()
    li=sort_humanly(li)
    t=''
    cnt=0
    usermail=get_username(session.get("logincookie"))
    for i in li:
        cnt+=1
        if(cnt>page*20):
            break
        if(cnt<=(page-1)*20):
            continue
        kk=json.loads(readf("./study/"+(i)))
        t+=f'''<tr onclick="window.open('/admin/studyedit/{i[:-5]}')" style="cursor:pointer;">
        <td>{i[:-5]}</td>
        <td>{kk['title']}</td>
        <td>{str(len(kk['content']))}</td></tr>'''
    return readf('./static/admin_temp.html').replace('<!-- title -->','学习管理').replace('<!-- documents -->',readf('./static/studyedit.html')).replace('<!-- lists -->',t)

@app.route('/admin/problemedit')
def admin_problemedit():
    if(not is_admin_cookie(session.get('logincookie'))):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html'))
    page=request.args.get("page")
    if(page==None):
        page=1
    page=int(page)
    li=get_problem_list()
    li=sort_humanly(li)
    t=''
    cnt=0
    usermail=get_username(session.get("logincookie"))
    for i in li:
        cnt+=1
        if(cnt>page*20):
            break
        if(cnt<=(page-1)*20):
            continue
        kk=get_problem(int(i))
        if(kk['type']=='contest'):
            kk['title']="<i>"+kk['title']+"(比赛赛题)</i>"
        if(kk['type']=='disabled'):
            kk['title']="<del>"+kk['title']+"(不可用)</del>"
        status={"passed":"✅","tried":"❌","none":" - "}
        t+='''<tr onclick="window.open('/admin/problemedit/{}')" style="cursor:pointer;">
        <td>{}</td><td>{}</td>
        <td><span class="tagchip mdui-text-truncate mdui-color-grey-800">{}</span></td>
        <td>{}</td></tr>'''.format(i,i,kk['title'],merge_tag(kk['tags']),ac_rate(i))
    return readf('./static/admin_temp.html').replace('<!-- title -->','题目编辑').replace('<!-- documents -->',readf('./static/problemedit.html')).replace('<!-- lists -->',t)

@app.route('/admin/dashboard')
def admin_dashboard():
    if(not is_admin_cookie(session.get('logincookie'))):
        return readf('./static/temp.html').replace('<!-- documents -->',readf('./static/no_auth.html'))
    return readf('./static/admin_temp.html').replace('<!-- title -->','仪表盘').replace('<!-- documents -->',readf('./static/dashboard.html'))

@app.errorhandler(404)  # 传入要处理的错误代码
def page_not_found(e):  # 接受异常对象作为参数
    return readf('./static/temp.html').replace('<!-- title -->','404').replace('<!-- documents -->',readf('./static/404.html')), 404  # 返回模板和状态码

@app.errorhandler(500)  # 传入要处理的错误代码
def internal_server_error(e):  # 接受异常对象作为参数
    return readf('./static/temp.html').replace('<!-- title -->','500').replace('<!-- documents -->',readf('./static/500.html')), 500  # 返回模板和状态码


if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5010,debug=True)

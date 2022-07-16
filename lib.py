from asyncio import ReadTransport
from xml.dom.minidom import parse
from markdown import markdown
import json
import html
import requests
import time
import _thread
import os
import re
import random,string
import smtplib
import email
import shutil
# 负责构造文本
from email.mime.text import MIMEText
# 负责构造图片
from email.mime.image import MIMEImage
# 负责将多个对象集合起来
from email.mime.multipart import MIMEMultipart
from email.header import Header

import difflib
import os
from PIL import Image

def antiSpider(request): # 每次请求时都会执行
    antiSpiderPage=""
    with open("./static/antispider.html",encoding="utf-8")as fp:
        antiSpiderPage=fp.read()
    user_agent = request.headers.get('User-Agent',"")
    if("python" in user_agent.lower()):#python默认爬虫
        return antiSpiderPage,403
    if(not user_agent): #空标头
        return antiSpiderPage,403

def get_activity_delta(usermail):
    j=json.loads(readf("activity.json"))
    if(usermail in j.keys()):
        return time.time()-j[usermail]
    return time.time()

def record_activity(usermail):
    j=json.loads(readf("activity.json"))
    j[usermail]=time.time()
    savef("activity.json",json.dumps(j))

def get_size(file):
    # 获取文件大小:KB
    size = os.path.getsize(file)
    return int(size / 1024)

def get_outfile(infile, outfile):
    if outfile:
        return outfile
    dir, suffix = os.path.splitext(infile)
    outfile = '{}-out{}'.format(dir, suffix)
    return outfile

def compress_image(infile, outfile='', mb=300, step=0.1, quality=20):
    """不改变图片尺寸压缩到指定大小
    :param infile: 压缩源文件
    :param outfile: 压缩文件保存地址
    :param mb: 压缩目标，KB
    :param step: 每次调整的压缩比率
    :param quality: 初始压缩比率
    :return: 压缩文件地址，压缩文件大小
    """
    o_size = get_size(infile)
    print(o_size)

    if o_size <= mb:
        return infile
    outfile = get_outfile(infile, outfile)
    while o_size > mb:
        im = Image.open(infile)
        im.save(outfile, quality=quality)
        if quality - step < 0:
            break
        quality -= step
        o_size = get_size(outfile)
    return outfile, get_size(outfile)

def real_compress(path):
    im=Image.open("./static/upload/"+path)#返回一个Image对象
    #os模块中的path目录下的getSize()方法获取文件大小，单位字节Byte
    size=os.path.getsize("./static/upload/"+path)/1024 #计算图片大小即KB
    print(size)
    #size的两个参数
    width,height=im.size[0],im.size[1]
    #用于保存压缩过程中的temp路径,每次压缩会被不断覆盖
    newPath="./static/upload/"+'temp_'+path
    while size>500:
        width, height = round(width * 0.9), round(height * 0.9)
        print(width,height)
        im = im.resize((width, height), Image.ANTIALIAS)
        im.save(newPath)
        size = os.path.getsize(newPath)/1024
    im.save("./static/upload/"+'compressed_'+path)
    try:
        os.remove(newPath)
        os.remove("./static/upload/"+path)
        os.rename("./static/upload/"+'compressed_'+path,"./static/upload/"+path)
    except:
        pass

def string_similar(s1, s2):
    return difflib.SequenceMatcher(None, s1, s2).quick_ratio()

import hashlib
# 哈希md5
def get_hash(string:str):
    return hashlib.md5(string.encode("utf-8")).hexdigest()

def genRandomString(slen=10):
    return ''.join(random.sample(string.ascii_letters + string.digits, slen))

def email2nickname(email):
    try:
        return json.loads(readf("./users/userandpass.json"))[email]['username']
    except:
        return None


def send_pl(sender,receiver): # 发送私信
    pass


def tryint(s):
    try:
        return int(s)
    except ValueError:
        return s

def str2int(v_str):
    v_str=str(v_str)
    return [tryint(sub_str) for sub_str in re.split('([0-9]+)', v_str)]

def real_follow(follower,followee): # 关注发起者，被关注者，使用email
    if(not is_following(follower,followee)):
        uid=email2usrid(follower)# follower uid
        msg={"user":email2nickname(follower),"msg":f'<a href="/user/{uid}">{email2nickname(follower)}</a> 关注了你'}
        send_notice(email2usrid(followee),"关注",time.time(),json.dumps(msg),f"/user/{email2usrid(followee)}")
    er=json.loads(readf("./users/follow_list.json")) # follow_list {"关注发起者":["被关注1","2"], ...}
    ee=json.loads(readf("./users/followed_list.json")) # followed {"被关注":["关注着1",..],..}
    if(follower not in er.keys()):
        er[follower]=[]
    if(followee not in ee.keys()):
        ee[followee]=[]
    if(followee not in er[follower]):
        er[follower].append(followee)
    if(follower not in ee[followee]):
        ee[followee].append(follower)
    savef("./users/follow_list.json",json.dumps(er))
    savef("./users/followed_list.json",json.dumps(ee))

def real_unfollow(follower,followee): # 关注发起者，被关注者，使用email
    er=json.loads(readf("./users/follow_list.json")) # follow_list {"关注发起者":["被关注1","2"], ...}
    ee=json.loads(readf("./users/followed_list.json")) # followed {"被关注":["关注着1",..],..}
    if(follower not in er.keys()):
        er[follower]=[]
    if(followee not in ee.keys()):
        ee[followee]=[]
    if(followee in er[follower]):
        er[follower].remove(followee)
    if(follower in ee[followee]):
        ee[followee].remove(follower)
    savef("./users/follow_list.json",json.dumps(er))
    savef("./users/followed_list.json",json.dumps(ee))

def is_following(follower,followee):
    er=json.loads(readf("./users/follow_list.json")) # follow_list {"关注发起者":["被关注1","2"], ...}
    if(follower not in er.keys()):
        er[follower]=[]
    return followee in er[follower]

def sort_humanly(v_list):
    return sorted(v_list, key=str2int)

def email2usrid(email):
    try:
        return json.loads(readf("./users/e2u.json"))[email]
    except:
        return "0"

def userid2email(userid):
    try:
        j=json.loads(readf("./users/e2u.json"))
        for i in j:
            if(j[i]==userid):
                return i
        return None
    except:
        return None

def get_problem_list():
    file_dir='./problemset'
    for kk,dirs,kkk in os.walk(file_dir):
        return dirs

def get_judgement_list():
    file_dir='./judgements'
    for kk,dirs,kkk in os.walk(file_dir):
        return kkk

def get_study_list():
    file_dir='./study'
    for kk,dirs,kkk in os.walk(file_dir):
        return kkk

def get_last_sid():
    li=get_study_list()
    li=sort_humanly(li)
    return li[len(li)-1]

def make_bandage_circle(color,icon,text):
    # 创建一个bandage的html
    # color: mdui-color-后面的内容
    # icon: mdui的图标名称
    # text:名字
    return '<button class="mdui-btn mdui-btn-icon mdui-btn-dense mdui-color-%color% mdui-ripple" mdui-tooltip="{content: \'%text%\', position: \'top\'}"><i class="mdui-icon material-icons">%icon%</i></button>'\
        .replace("%color%",color).replace("%icon%",icon).replace("%text%",text)
def get_problem_old(problem_id):
    ret={}
    dom=parse('./problemset/{}/des.xml'.format(str(problem_id)))
    data=dom.documentElement
    ret['title']=(data.getElementsByTagName('title')[0].childNodes[0].nodeValue)
    ret['tag']=(data.getElementsByTagName('tag')[0].childNodes[0].nodeValue)
    ret['time_limit']=(data.getElementsByTagName('time_limit')[0].childNodes[0].nodeValue)
    ret['memory_limit']=(data.getElementsByTagName('memory_limit')[0].childNodes[0].nodeValue)
    getlist=['background','description','tips','input','output']
    for i in getlist:
        try:
            ret[i]=markdown(data.getElementsByTagName(i)[0].childNodes[0].nodeValue)
        except:
            ret[i]=''
    sample=data.getElementsByTagName('data')
    ret['sample']={}
    count=0
    for sam in sample:
        count+=1
        ret['sample'][count]={}
        try:
            ret['sample'][count]['input']=sam.getElementsByTagName('sample_input')[0].childNodes[0].nodeValue
        except:
            ret['sample'][count]['input']=''
        try:
            ret['sample'][count]['output']=sam.getElementsByTagName('sample_output')[0].childNodes[0].nodeValue
        except:
            ret['sample'][count]['output']=''
    return ret

def get_problem(problemid):
    j=json.loads(readf("./problemset/"+str(problemid)+"/problem.json"))
    if(not "type" in j.keys()):
        j['type']="problem"
    return j

def merge_tag(tag_list):
    ret=''
    for i in tag_list:
        ret+=i+','
    return ret[:-1]

def ac_rate(problemid):
    j=json.loads(readf("./problemset/"+str(problemid)+"/status.json"))
    cnt_all=0
    cnt_ac=0
    for i in j:
        cnt_all+=i['value']
        if(i['name']=='AC'):
            cnt_ac=i['value']
    if(cnt_all==0):
        return "-"
    else:
        return str(round(100*cnt_ac/cnt_all,2))+"%"
    

def readf(path):
    with open(path,'r',encoding='utf-8') as f:
        return f.read()

def get_judgement(task_id):
    if(os.path.exists('./judgements/'+str(task_id)+'.json')):
        return {"status":"ok","info":json.loads(readf('./judgements/'+str(task_id)+'.json'))}
    else:
        return {"status":"file_not_found"}

def savef(path,text):
    if(type(text) == dict):
        text=json.dumps(text)
    with open(path,'w',encoding='utf-8') as f:
        return f.write(text)

def setstatus(task_id,msg): # 设置评测状态
    savef('./judgements/'+str(task_id)+'.json',msg)
    return msg

def setlang(task_id,language,username): # 设置测评语言和用户
    j=json.loads(readf('./judgements/'+str(task_id)+'.json'))
    j['language']=language
    j['username']=username
    setstatus(task_id,json.dumps(j))

def setproid(task_id,proid): # 设置测评语言和用户
    j=json.loads(readf('./judgements/'+str(task_id)+'.json'))
    j['problem_id']=int(proid)
    setstatus(task_id,json.dumps(j))

def user_exist(username):
    l=json.loads(readf('./users/userandpass.json'))
    for i in l:
        if(l[i]['username']==username):
            return True
    return False

def nick_to_email(name):
    l=json.loads(readf('./users/userandpass.json'))
    for i in l:
        if(l[i]['username']==name):
            return i
    return ""
def safe_redirect(path):
    return f"<script>location.href=\"{path}\"</script>"
def mail_exist(mail):
    l=json.loads(readf('./users/userandpass.json'))
    return mail in l.keys()

def is_taking_part_in(cid,usermail):
    c=json.loads(readf("./contest/"+str(cid)+'.json'))
    return (usermail in c['participants'])

def total_score(s):
    sc=0
    for i in s[1].keys():
        sc+=s[1][i]['score']
    return sc

def total_try(s):
    sc=0
    for i in s[1].keys():
        sc+=s[1][i]['tried_times']
    return sc

def cookie_valid(lcookie):
    j=json.loads(readf("./users/logincookie.json"))
    if(lcookie in j.keys()):
        if(time.time()<=j[lcookie]['time']):
            return True
        else:
            return False
    else:
        return False

def get_username(lcookie):
    if(lcookie==None):
        return None
    elif(not cookie_valid(lcookie)):
        return None
    else:
        return get_profile(lcookie)['username']
        
def is_admin_name(uname):
    userandpass=json.loads(readf('./users/userandpass.json'))
    for i in userandpass:
        if(userandpass[i]["username"]==uname):
            adminflag=userandpass[i].get("admin")
            if(adminflag):
                return True
            else:
                return False
    return False
def is_admin_email(email):
    userandpass=json.loads(readf('./users/userandpass.json'))
    x=userandpass.get(email)
    if(not x):
        return False
    if(x.get("admin")!=None):
        return True
    return False

def is_admin_cookie(lcookie):
    if(lcookie==None):
        return False
    elif(not cookie_valid(lcookie)):
        return False
    else:
        email=get_profile(lcookie)['username']
        return is_admin_email(email)

def askcmp(x,y):
    return x['liked']>y['liked']

def get_oneword_byemail(user):
    return json.loads(readf('./users/'+email2usrid(user)+'/profile.json'))['oneword']

def get_profile(lcookie):
    # username是email
    j=json.loads(readf("./users/logincookie.json"))
    u=j[lcookie]
    username=u['username']
    userid=email2usrid(username)
    return {"username":username,"userid":userid}

def verify_captcha(cap):
    re=requests.post(url="https://www.recaptcha.net/recaptcha/api/siteverify?secret=6LeXLiIeAAAAAFG3yOR9vd6zl_4Fp4SSX7DD_LYw&response="+cap)
    print(json.loads(re.text)['success'])
    return (json.loads(re.text)['success'])

def send_email(receiver,title,content):
    print('''sudo mail -s "{}" "{}" <<< "{}" -aFrom:noreply@amzcd.top'''.format(title,receiver,content))
    k=os.system('''sudo mail -s "{}" "{}" <<< "{}" -aFrom:noreply@amzcd.top'''.format(title,receiver,content))
    print(k)

def get_user_amount(path='./users'):
    # count = 0
    # for root,dirs,files in os.walk(path):    #遍历统计
    #     for each in files:
    #             count += 1   #统计文件夹下文件个数
    return len([lists for lists in os.listdir(path) if os.path.isdir(os.path.join(path, lists))])

def send_email_fake(receiver,mail_title,mail_content):
    print("send_email")
    #Yandex邮箱smtp服务器
    host_server = 'smtp.yandex.com'
    #Yandex邮箱smtp服务器端口
    ssl_port = '465'
    #用户名
    user = 'amzcd.service@yandex.com'
    #pwd为密码
    pwd = 'Zyq20071027'
    #发件人的邮箱
    sender_mail = 'amzcd.service@yandex.com'
    # ssl登录
    smtp = smtplib.SMTP(host_server)
    smtp = smtplib.SMTP_SSL(host_server, ssl_port)
    # set_debuglevel()是用来调试的。参数值为1表示开启调试模式，参数值为0关闭调试模式
    smtp.set_debuglevel(1)
    smtp.ehlo(host_server)
    smtp.login(user, pwd)
    msg = MIMEText(mail_content, "plain", 'utf-8')
    msg["Subject"] = Header(mail_title, 'utf-8')
    msg["From"] = sender_mail
    msg["To"] = receiver
    smtp.sendmail(sender_mail, receiver, msg.as_string())

def is_valid_nickname(nickname):
    invalid=[' ','&',';','<','>','%','\'','`','"']
    if(len(nickname)==0):
        return False
    for i in invalid:
        if(i in nickname):
            return False
    # check if there is unvisable char in nickname
    if(not nickname.isprintable()):
        return False
    return True

def is_valid_email(email):
    # ex_email = re.compile(r'^[\w][a-zA-Z1-9._]{4,19}@[a-zA-Z0-9]{2,3}.[com|gov|net]')
    # result = ex_email.match(email)
    # if result:
    #     return True
    # else:
    #     return False
    if(email.find("@")!=-1):
        return True
    return False

def parse_email_domain(email):
    return email[email.rfind("@")+1:]

def random_ch_char():
    val = random.randint(0x4e00, 0x9fbf)
    return chr(val)

def random_ch_str(length):
    ret=''
    for i in range(length):
        ret+=random_ch_char()
    return ret

def raw_string(str):
    escape_dict = {    '\a': r'\a',
                   '\b': r'\b',
                   '\c': r'\c',
                   '\f': r'\f',
                   '\n': r'\n',
                   '\r': r'\r',
                   '\t': r'\t',
                   '\v': r'\v',
                   '\'': r'\'',
                   '\"': r'\"',
                   '\0': r'\0',
                   '\1': r'\1',
                   '\2': r'\2',
                   '\3': r'\3',
                   '\4': r'\4',
                   '\5': r'\5',
                   '\6': r'\6',
                   '\7': r'\7',
                   '\8': r'\8',
                   '\9': r'\9'}
    rstring = ""
    for char in str:         # 防止图片地址发生转义
        try:
            if char in escape_dict:
                rstring += escape_dict[char]
            else:
                rstring += char
        except:
            print("字符串变量转义发生错误")
    return (rstring)

def waiting(username,password,email,url,timee):
    j=json.loads(readf("./users/waiting.json"))
    j[url]={'username':username,'password':password,'email':email,'time':timee}
    savef('./users/waiting.json',json.dumps(j))

def set_lcookie(lcookie,username,timee):
    j=json.loads(readf("./users/logincookie.json"))
    j[lcookie]={'username':username,'time':timee}
    savef('./users/logincookie.json',json.dumps(j))

def COLOR(status):
    COLORLIST={"Accepted":"light-green","Wrong Answer":"red","Partial Accepted":"blue","Compile Error":"yellow","Time Limit Exceeded":"brown"}
    if(status in COLORLIST):
        return COLORLIST[status]
    else:
        return "grey"

def get_full_score(pid):
    p=get_problem(pid)
    s=0
    for i in p['test_case_score']:
        s+=i['score']
    return s

def get_chat_list():
    file_dir='./chat/benben'
    for kk,dirs,kkk in os.walk(file_dir):
        return kkk

def get_contest_list():
    file_dir='./contest'
    for kk,dirs,kkk in os.walk(file_dir):
        return kkk

def get_data_list(pid):
    file_dir='./problemset/'+str(pid)+'/testcase'
    for kk,dirs,kkk in os.walk(file_dir):
        return kkk

def get_ask_list():
    file_dir='./ask/aq'
    for kk,dirs,kkk in os.walk(file_dir):
        return kkk

def get_art_list():
    file_dir='./article/psg'
    for kk,dirs,kkk in os.walk(file_dir):
        return kkk

def new_benben(username,md):
    f={"user":username,"info":md,"reply":[],"time":time.time(),"liked":0,"who_liked":[],"rebenben":0}
    bid=json.loads(readf("./chat/config.json"))
    bid['amount']+=1
    savef('./chat/benben/{}.json'.format(bid['amount']),json.dumps(f))
    savef('./chat/config.json',json.dumps(bid))
    return bid['amount']

def like_benben(username,benbenid):
    f=json.loads(readf('./chat/benben/{}.json'.format(str(benbenid))))
    f['liked']+=1
    f['who_liked'].append(username)
    savef('./chat/benben/{}.json'.format(str(benbenid)),json.dumps(f))

def rebenben_benben(username,benbenid):
    f=json.loads(readf('./chat/benben/{}.json'.format(str(benbenid))))
    f['rebenben']+=1
    savef('./chat/benben/{}.json'.format(str(benbenid)),json.dumps(f))

def add_reply(username,benbenid,replyid):
    f=json.loads(readf('./chat/benben/{}.json'.format(str(benbenid))))
    f['reply'].append(replyid)
    savef('./chat/benben/{}.json'.format(str(benbenid)),json.dumps(f))

def get_benben_user(benbenid):
    return json.loads(readf('./chat/benben/{}.json'.format(str(benbenid))))['user']
def get_bandages_by_userdat(userdat,email):
    bandages=[] # 这个以后可以考虑一下存储？ 已经添加
    if(is_admin_email(email)):
        bandages.append(make_bandage_circle("blue","supervisor_account","TasOJ Admin!"))
    for i in userdat["bandages"]:
        bandages.append(make_bandage_circle(i["color"],i["icon"],i["text"]))
    return bandages
def get_bandages_by_email(email):
    userdat=json.loads(readf('./users/userandpass.json'))[email]
    return get_bandages_by_userdat(userdat)
def get_bandages_by_id(uid):
    email=userid2email(uid)
    userdat=json.loads(readf('./users/userandpass.json'))[email]
    return get_bandages_by_userdat(userdat)
def create_new_account(userid):
    filelist=['avatar.png','header.png','introduction.md','profile.json','train.json','notice.json','private.json']
    for i in filelist:
        shutil.copyfile('./users/'+i,'./users/'+userid+'/'+i)

def get_last_pid():
    li=get_problem_list()
    li=sort_humanly(li)
    return li[len(li)-1]

def get_benben_list():
    amount=json.loads(readf("./chat/config.json"))['amount']
    return range(amount,0,-1)

def get_user_list():
    amount=get_user_amount()
    return range(1,amount+1)

def search_benben(q):
    li=get_benben_list()
    ret=[]
    for i in li:
        p=json.loads(readf("./chat/benben/"+str(i)+".json"))
        if(time.time()-float(p['time'])>2592000):
            break
        if(string_similar(p['info'],q)>=0.7 or (q in p['info'])):
            p["benbenid"]=str(i)
            ret.append(p)
    return ret

def search_user(q):
    li=get_user_list()
    ret=[]
    for i in li:
        p=(readf("./users/"+str(i)+"/introduction.md"))
        # print(userid2email(str(i)))
        if(string_similar(p,q)>=0.3 or (q in p) or q==email2nickname((userid2email(str(i))))):
            ret.append({"userid":str(i)})
    return ret

def search_ask(q):
    li=get_ask_list()
    ret=[]
    if(q.find("problemid:")!=-1):
        pid=q[q.find("problemid:")+10:]
        for i in li:
            p=json.loads(readf("./ask/aq/"+str(i)))
            if(time.time()-float(p['time'])>2592000):
                break
            if((str(p['pid'])==pid)):
                p["askid"]=str(i)[:-5]
                ret.append(p)
        return ret
    for i in li:
        p=json.loads(readf("./ask/aq/"+str(i)))
        if(time.time()-float(p['time'])>2592000):
            break
        if(string_similar(p['question'],q)>=0.3 or (q in p['question']) or string_similar(p['title'],q)>=0.7):
            p["askid"]=str(i)[:-5]
            ret.append(p)
    return ret

def search_art(q):
    li=get_art_list()
    ret=[]
    if(q.find("problemid:")!=-1):
        pid=q[q.find("problemid:")+10:]
        for i in li:
            p=json.loads(readf("./article/psg/"+str(i)))
            if(time.time()-float(p['time'])>2592000):
                break
            if((str(p['pid'])==pid)):
                p["askid"]=str(i)[:-5]
                ret.append(p)
        return ret
    for i in li:
        p=json.loads(readf("./article/psg/"+str(i)))
        if(time.time()-float(p['time'])>2592000):
            break
        if(string_similar(p['question'],q)>=0.3 or (q in p['question']) or string_similar(p['title'],q)>=0.7):
            p["askid"]=str(i)[:-5]
            ret.append(p)
    return ret

def get_problem_sum():
    return len(os.listdir("./problemset"))

def get_random_problem():
    return os.listdir("./problemset")[random.randint(0,get_problem_sum()-1)]

def develop_problem_index():
    li=get_problem_list()
    index={}
    # index: {{1000:{"title":"hw","tags":["123","e"]}},{1001:{"title":"ab","tags":["123","e"]}}}
    for i in li:
        p=json.loads(readf("./problemset/"+str(i)+"/problem.json"))
        index[int(i)]={"title":p['title'],"tags":p['tags']}
    savef("./indexes/problem_index.json",json.dumps(index))

def search_problem(q):
    _thread.start_new_thread( develop_problem_index, ( ) )
    li=get_problem_list()
    ret=[]
    pindex=json.loads(readf("./indexes/problem_index.json"))
    if(q.find("tag:")!=-1):
        pid=q[q.find("tag:")+4:]
        for i in li:
            if(pid in pindex[str(i)]['tags']):
                p=json.loads(readf("./problemset/"+i+"/problem.json"))
                p["problemid"]=i
                ret.append(p)
        return ret
    for i in li:
        if(string_similar(pindex[str(i)]['title'],q)>=0.8 or i==q):
            p=json.loads(readf("./problemset/"+i+"/problem.json"))
            p["problemid"]=i
            ret.append(p)
    return ret

def develop_judgement_index():
    li=get_judgement_list()
    index={}
    for i in li:
        p=json.loads(readf("./judgements/"+str(i)))
        if(time.time()-float(i[:-5])>2592000):
            break
        if(int(p['problem_id']) not in index.keys()):
            index[int(p['problem_id'])]=[]
        index[int(p['problem_id'])].append({"status":p['status'],"usermail":p['username'],"jid":i[:-5]})
    savef("./indexes/judgement_index.json",json.dumps(index))

def develop_judgement_index_by_user():
    li=get_judgement_list()
    index={}
    for i in li:
        p=json.loads(readf("./judgements/"+str(i)))
        if(time.time()-float(i[:-5])>2592000):
            break
        if((p['username']) not in index.keys()):
            index[(p['username'])]=[]
        index[(p['username'])].append({"status":p['status'],"jid":i[:-5]})
    savef("./indexes/judgement_index_user.json",json.dumps(index))

def search_judgement(q):
    _thread.start_new_thread( develop_judgement_index, ( ) )
    _thread.start_new_thread( develop_judgement_index_by_user, ( ) )
    ret=[]
    if(q.find(" ")!=-1):
        li=json.loads(readf("./indexes/judgement_index.json"))
        u=q.split(" ")[0]
        v=q.split(" ")[1]
        if(u in li.keys()):
            temp=v
            v=u
            u=temp
        # 使得v一定是题目编号
        if((v) in li.keys()):
            for j in li[v]:
                if((email2nickname(j['usermail'])==u)):
                    # print(p['username'],p['problem_id'])
                    p=json.loads(readf("./judgements/"+j['jid']+".json"))
                    p["judgeid"]=j['jid']
                    ret.append(p)
        # print(ret)
        return ret
    elif(q.find("problemid:")!=-1):
        li=json.loads(readf("./indexes/judgement_index.json"))
        pid=q[q.find("problemid:")+10:]
        for i in li[str(pid)]:
            p=json.loads(readf("./judgements/"+i['jid']+'.json'))
            p["judgeid"]=i['jid']
            ret.append(p)
        return ret
    li=json.loads(readf("./indexes/judgement_index_user.json"))
    q=nick_to_email(q)
    if((q) in li.keys()):
        for j in li[q]:
            p=json.loads(readf("./judgements/"+j['jid']+".json"))
            p["judgeid"]=j['jid']
            ret.append(p)
    return ret

def get_noti(userid):
    return json.loads(readf("./users/"+str(userid)+"/notice.json"))

def read_all(userid):
    n=get_noti(userid)
    r=n['unread']
    n['unread']=[]
    for i in r:
        n['read'].insert(0,i)
    savef("./users/"+str(userid)+"/notice.json",json.dumps(n))

def send_notice(userid,typee,timee,msg,link):
    try:
        data=json.loads(msg)
        if(data["user"]==email2nickname(userid2email(userid)) and not data.get("ignoreMe")):
            return
    except:
        pass
    n=get_noti(userid)
    n['unread'].append({"type":typee,"time":timee,"msg":msg,"link":link})
    savef("./users/"+str(userid)+"/notice.json",json.dumps(n))

def passed_problem(usermail,pid):
    if(usermail==None):
        return 'none'
    userid=email2usrid(usermail)
    j=json.loads(readf("./users/"+str(userid)+"/train.json"))
    # print(j,pid)
    if(int(pid) in j['passed']):
        return 'passed'
    elif(int(pid) in j['tried']):
        return 'tried'
    else:
        return 'none'

def record_tags():
    li=get_problem_list()
    tag_list=[]
    for i in li:
        p=json.loads(readf("./problemset/"+i+"/problem.json"))
        tags=p['tags']
        for j in tags:
            if(j not in tag_list):
                tag_list.append(j)
    savef("./indexes/tag_list.json",json.dumps(tag_list))

def get_problem_tags():
    _thread.start_new_thread( record_tags, ( ) )
    return json.loads(readf("./indexes/tag_list.json"))
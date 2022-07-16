obj={};
var userProfileRe = new XMLHttpRequest();//第一步：创建需要的对象
userProfileRe.open('GET', '/get_profile', true); //第二步：打开连接/***发送json格式文件必须设置请求头 ；如下 - */
userProfileRe.setRequestHeader("Content-type", "application/json");//设置请求头 注：post方式必须设置请求头（在建立连接后设置请求头）var obj = { name: 'zhansgan', age: 18 };
userProfileRe.send(JSON.stringify(obj));//发送请求 将json写入send中
userProfileRe.onreadystatechange = function () {//请求后的回调接口，可将请求成功后要执行的程序写在其中
    if (userProfileRe.readyState == 4 && userProfileRe.status == 200) {//验证请求是否发送成功
        var json = userProfileRe.responseText;//获取到服务端返回的数据
        console.log(kk = JSON.parse(json));
        if(kk['status']=='failed'){
            document.getElementById('loginn').removeAttribute('hidden');
            document.getElementById('registerr').removeAttribute('hidden');
        }else{
            document.getElementById('loginn').remove();
            document.getElementById('registerr').remove();
            document.getElementById('ppp').removeAttribute('hidden');
            document.getElementById('ppp2').removeAttribute('hidden');
            username=kk['msg']['username'];
            userid=kk['msg']['userid'];
            document.getElementById('avatar').setAttribute('src','/users/'+username+'/avatar.png');
            document.getElementById('ppp').setAttribute('onclick',"location.href='/user/"+userid+"';");
            // document.getElementById('ppp').setAttribute('mdui-tooltip','{"content":"已登录：'+username+'"}');
        }
    }
};



obj2={};
var nore = new XMLHttpRequest();//第一步：创建需要的对象
nore.open('GET', '/unread_number', true); //第二步：打开连接/***发送json格式文件必须设置请求头 ；如下 - */
nore.setRequestHeader("Content-type", "application/json");//设置请求头 注：post方式必须设置请求头（在建立连接后设置请求头）var obj = { name: 'zhansgan', age: 18 };
nore.send(JSON.stringify(obj2));//发送请求 将json写入send中
nore.onreadystatechange = function () {//请求后的回调接口，可将请求成功后要执行的程序写在其中
    if (nore.readyState == 4 && nore.status == 200) {//验证请求是否发送成功
        var json = nore.responseText;//获取到服务端返回的数据
        if(Number(json)>0){
            document.getElementById("cnt").removeAttribute("hidden");
            document.getElementById("ppp2").setAttribute("mdui-tooltip",`{content: '`+json+`条未读消息'}`)
        }
    }
};





var inst = new mdui.Drawer('#drawer');

// method

document.getElementById('open').addEventListener('click', function () {
    inst.open();
});

document.getElementById('close').addEventListener('click', function () {
    inst.close();
});

document.getElementById('toggle').addEventListener('click', function () {
    inst.toggle();
});

document.getElementById('getState').addEventListener('click', function () {
    mdui.alert(inst.getState());
});

// event
var drawer = document.getElementById('drawer');
drawer.addEventListener('open.mdui.drawer', function () {
    console.log('open');
});
drawer.addEventListener('opened.mdui.drawer', function () {
    console.log('opened');
});
drawer.addEventListener('close.mdui.drawer', function () {
    console.log('close');
});
drawer.addEventListener('closed.mdui.drawer', function () {
    console.log('closed');
});

function register() {
    location.href = '/register';
}

function login() {
    location.href = '/login';
}
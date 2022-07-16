setTimeout(function () {
    rs=document.getElementById("realstatus").innerText.replaceAll(' ','').replaceAll('\n','');
    if (rs == "Judging" || rs == "Compiling" || rs == "Waiting") {
        mdui.dialog({
            title: '正在测评中',
            content: `<div class="mdui-progress">
            <div class="mdui-progress-indeterminate"></div>
          </div><br>稍安勿躁……<br>将会为您自动刷新`,
            buttons: []
        });
        setTimeout(function () {
            location.reload();
        }, 2333);
    }
}, 500);

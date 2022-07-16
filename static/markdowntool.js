// 请先导入showdown,hljs
function markdown_render_dom(dom, text) {
    var config = {
        parseImgDimensions: true,
        simplifiedAutoLink: true,
        simpleLineBreaks: true,
        requireSpaceBeforeHeadingText: false,
        openLinksInNewWindow: true,
    }
    const classMap = {
        table: 'mdui-table',
    }
    let exts = [];
    const bindings = Object.keys(classMap)
        .map(key => ({
            type: 'output',
            regex: new RegExp(`<${key}(.*)>`, 'g'),
            replace: `<${key} class="${classMap[key]}" $1>`
        }));
    exts = exts.concat(bindings)
    const antixxs = {
        type: 'output',
        filter: function (text, converter, options) {
            // text=text.replace(/<\/?style>/g, '');
            return filterXSS(text);
         }
    }
    exts.push(antixxs);
    // exts.push(username)
    var converter = new showdown.Converter({
        extensions: exts,
        ghMentionsLink: "/user_byname/{u}"
    });
    converter.setFlavor("github")
    for (i in config) {
        converter.setOption(i, config[i]);
    }
    let html = converter.makeHtml(text);
    dom.innerHTML = html;
    mdui.mutation(dom);
    $('pre code').each(function(i, block) {
        hljs.highlightBlock(block);
    });
}
import requests
from bs4 import BeautifulSoup
from mako.template import Template
import re
from hashlib import md5
import gzip
from json import dumps

RE_FONT = re.compile('font-family:[^;"]+')


def fetch_list(n):
    url = "http://newsblog.chinatimes.com/duduong/cn/p%s" % n
    print(url)
    r = requests.get(url)
    doc = BeautifulSoup(r.content)
    li = []
    for h2 in doc.find_all('h2'):
        a = h2.find('a')
        if not a:
            continue

        href = a.attrs['href']
        id = href.split("/")[-1]
        r = requests.get("http://newsblog.chinatimes.com/" + href)
        content = r.content.decode('utf-8')
        # with open("org/%s.html"%id, "w") as f:
        #     f.write(content)
        print(id)
        content = RE_FONT.sub('', content)
        r = parse(id, content)
        li.append(r)
    return li


INDEX = Template("""
<!DOCTYPE html><html><head><meta content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no" name=viewport><meta charset=utf-8>
<link rel="stylesheet" href="/html/init.css">
<style>
.LI li{
list-style-type: disc;
}
.LI li{
margin-bottom:8px;
}
.LI a{
text-decoration: none;
}
.LI .title{
color:#000;
}
.LI .title:hover{
color:#f40;
}
.LI .date{
font-size:12px;
color:#999;
float:right;
}
</style>
</head>
<body><div class="BODY">
<h1>王孟源的博客</h1>
<ul class="LI">
%for url, name in li:
<li><a class="title" href="/${url}">${name}</a><a class="date" href="/${url}">${url[5:15]}</a></li>
%endfor
</ul>
</div></body></html>
""")

HTML = Template("""<!DOCTYPE html><html><head><meta content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no" name=viewport><meta charset=utf-8>
<link rel="stylesheet" href="./init.css">
</head>
<body><div class="BODY">
<div class="BACK"><a href="/">返回索引页</a></div>
<h1>${title}</h1>
<p class="DATE">${date}</p>
<div class="POST">${post}</div>
<div class="REPLY_LI">
%for say, reply, user, time in reply_li:
<div class="LI">
<div class="USER"><span class="NAME">${user}</span><div class="TIME">${time}</div></div>
<div class="SAY">${say}</div>
%if reply:
<div class="REPLY">${reply}</div>
%endif
</div>
%endfor
</div>
</div>
<div class="BACK"><a href="/">返回索引页</a></div>
</body></html>""")

# HTML = Template("""
# <div class="POST" style="font-size:16px">${post}</div>
# <p class="DATE">发表日期 : ${date}</p>
# <div class="REPLY_LI">
# %if reply_li:
# <hr>
# <h2>${len(reply_li)} 条留言</h2>
# %for say, reply, user, time in reply_li:
# <hr>
# <div class="LI" style="font-size:16px">
# <p style="font-size:16px;font-weight:bold" class="USER"><span class="NAME">${user} 留言 : </span></p>
# <div style="font-size:16px" class="SAY">${say} (${time})</div>
# %if reply:
# <p style="font-size:16px;font-weight:bold">王孟源 回复:</p>
# <pstyle="font-size:16px" class="REPLY">${reply}<p>
# %endif
# </div>
# %endfor
# %endif
# </div>
# """)

def parse(id, html):
    doc = BeautifulSoup(html)

    title = doc.title.text.rsplit("-", 1)[0]
    post = doc.find(class_='part-02')
    for i in post.find_all('img'):
        src = i.attrs['src']
        if src and src.startswith("/"):
            print(src)
        url = "http://newsblog.chinatimes.com/%s" % src
        img = requests.get(url).content
        url = "/img/%s.%s" % (md5(img).hexdigest(), src.rsplit(".", 1)[-1])
        with open("html%s" % url, "wb") as f:
            f.write(img)
        i.attrs['src'] = "." + url

    reply_li = []
    for i in doc.find_all(class_='comment'):
        text = i.find(class_='text')
        reply = text.find(class_='reply')
        if reply:
            reply.extract()
        ul = i.find('ul')
        time, user = (i for i in ul.contents if i.name == 'li')
        text = text.decode_contents(formatter="html").strip()

        if reply:
            reply = reply.decode_contents(formatter="html").strip()
        else:
            reply = ''
        reply_li.append(
            (
                text,
                reply,
                user.text,
                time.text.strip(' :'),
            )
        )
    date = post.find('ul').text.strip()
    post = post.find(class_='articlebox')
    for tag in post:
        if hasattr(tag, 'attrs'):
            for attribute in ["class", "id", "name"]:
                if attribute in tag.attrs:
                    del tag.attrs[attribute]

    filepath = "html/%s.%s.html" % (date.replace(':',
                                                 "-").replace(" ", "_"), id)
    with open(filepath, "w") as f:
        f.write(
            HTML.render(
                title=title,
                date=date,
                post=post,
                reply_li=reply_li
            )
        )

    return [
        filepath,
        title,
        date,
        str(post),
        reply_li
    ]


def main():
    li = []
    for i in range(1, 5):
        li.extend(fetch_list(i))
    with gzip.open("html/data.json.gz", "wb") as data:
        for i in li:
            s = dumps(i, ensure_ascii=False) + "\n"
            data.write(s.encode('utf-8'))
    with open("index.html", "w") as index:
        index.write(INDEX.render(li=[i[:2] for i in li]))


main()

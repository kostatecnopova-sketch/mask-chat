from flask import Flask, render_template_string, request, jsonify
import sqlite3, time, os

app = Flask(__name__)
app.config["SECRET_KEY"] = "mask"

DB = "/tmp/mask.db"

def init():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS waiting(user_id TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS chats(id INTEGER PRIMARY KEY AUTOINCREMENT, user1 TEXT, user2 TEXT, active INT)")
    c.execute("CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INT, sender TEXT, text TEXT, ts INT)")
    conn.commit()
    conn.close()

init()

POLICY = """Политика конфиденциальности Mask 🎭

1. Сервис предназначен для анонимного общения. Мы не собираем личные данные пользователей.

2. Администрация не несёт ответственности за содержание сообщений, передаваемых между пользователями. Вся ответственность за отправляемый контент лежит на отправителе.

3. Запрещено: распространение незаконного контента, угрозы, спам, оскорбления, пропаганда насилия.

4. Используя сервис, вы соглашаетесь с данной политикой."""

HTML_MAIN = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>Mask</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;width:100%;position:fixed;overflow:hidden}
body{font-family:Arial;background:#000}
#main-bg{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0}
#main{position:relative;z-index:1;display:flex;flex-direction:column;height:100%;max-width:800px;margin:0 auto;width:100%}
#top{background:#202c33;padding:10px 16px;color:white;font-weight:bold;font-size:17px;flex-shrink:0;display:flex;justify-content:space-between}
#center{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:20px}
#search-btn{background:#00a884;color:white;border:none;padding:15px 40px;font-size:20px;border-radius:30px;cursor:pointer}
#searching{display:none;color:white;font-size:24px;text-align:center}
#limit{display:none;color:red;font-size:18px;text-align:center}
.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);z-index:999;align-items:center;justify-content:center}
.modal-content{background:#202c33;color:white;padding:20px;border-radius:10px;max-width:90%;max-height:80%;overflow-y:auto;margin:20px}
.modal-title{font-size:20px;font-weight:bold;margin-bottom:15px}
.modal-text{font-size:14px;line-height:1.5;white-space:pre-line;margin-bottom:20px}
.modal-check{display:flex;align-items:center;gap:10px;margin-bottom:20px;font-size:14px}
.modal-check input{width:20px;height:20px}
.modal-btn{background:#00a884;color:white;border:none;padding:12px 30px;font-size:16px;border-radius:25px;cursor:pointer;width:100%}
.modal-btn:disabled{opacity:0.5;cursor:not-allowed}
@keyframes dots{0%,20%{opacity:1}40%{opacity:0}60%{opacity:0}80%{opacity:0}100%{opacity:1}}
.dot1{animation:dots 1.5s infinite}
.dot2{animation:dots 1.5s 0.3s infinite}
.dot3{animation:dots 1.5s 0.6s infinite}
</style>
</head>
<body>
<canvas id="main-bg"></canvas>
<div id="main">
<div id="top"><span>Mask 🎭</span><span id="stats">0 online | 0 search | 0 chats</span></div>
<div id="center">
<button id="search-btn" onclick="showPolicy()">🔍 Начать поиск</button>
<div id="searching">Поиск собеседника<span class="dot1">.</span><span class="dot2">.</span><span class="dot3">.</span></div>
<div id="limit">Лимит онлайна</div>
</div>
</div>
<div class="modal" id="policy-modal">
<div class="modal-content">
<div class="modal-title">Политика конфиденциальности</div>
<div class="modal-text">""" + POLICY + """</div>
<div class="modal-check">
<input type="checkbox" id="agree-check" onchange="document.getElementById('agree-btn').disabled=!this.checked">
<label for="agree-check">Я согласен с политикой конфиденциальности</label>
</div>
<button class="modal-btn" id="agree-btn" disabled onclick="agreeAndSearch()">Продолжить</button>
</div>
</div>
<script>
var uid=localStorage.getItem("uid")||("U"+Math.random().toString(36).substr(2,9));
localStorage.setItem("uid",uid);

var canvas=document.getElementById("main-bg");
var ctx=canvas.getContext("2d");
canvas.width=window.innerWidth;
canvas.height=window.innerHeight;
var stars=[];
for(var i=0;i<200;i++){stars.push({x:Math.random()*canvas.width,y:Math.random()*canvas.height,s:Math.random()*2+0.5,o:Math.random()});}
var meteors=[];
var meteorTimer=0;

function draw(){
    ctx.clearRect(0,0,canvas.width,canvas.height);
    ctx.fillStyle="#000";ctx.fillRect(0,0,canvas.width,canvas.height);
    stars.forEach(s=>{
        s.o+=0.01;if(s.o>1)s.o=0;
        var glow=ctx.createRadialGradient(s.x,s.y,0,s.x,s.y,s.s*3);
        glow.addColorStop(0,"rgba(255,255,255,"+s.o+")");
        glow.addColorStop(0.5,"rgba(255,255,255,"+(s.o*0.5)+")");
        glow.addColorStop(1,"rgba(255,255,255,0)");
        ctx.fillStyle=glow;ctx.beginPath();ctx.arc(s.x,s.y,s.s*3,0,Math.PI*2);ctx.fill();
        ctx.fillStyle="rgba(255,255,255,"+s.o+")";ctx.beginPath();ctx.arc(s.x,s.y,s.s,0,Math.PI*2);ctx.fill();
    });
    meteorTimer++;
    if(meteorTimer>=120){
        meteors.push({x:Math.random()*canvas.width,y:-20,size:Math.random()*3+2,speed:Math.random()*3+2,trail:[],life:1});
        meteorTimer=0;
    }
    for(var i=meteors.length-1;i>=0;i--){
        var m=meteors[i];m.y+=m.speed;m.x+=m.speed*0.3;
        m.trail.push({x:m.x,y:m.y});if(m.trail.length>20)m.trail.shift();
        ctx.save();ctx.globalAlpha=m.life;
        if(m.trail.length>1){for(var j=1;j<m.trail.length;j++){var alpha=j/m.trail.length*0.5;ctx.strokeStyle="rgba(0,200,100,"+alpha+")";ctx.lineWidth=m.size*(j/m.trail.length);ctx.beginPath();ctx.moveTo(m.trail[j-1].x,m.trail[j-1].y);ctx.lineTo(m.trail[j].x,m.trail[j].y);ctx.stroke();}}
        var headGlow=ctx.createRadialGradient(m.x,m.y,0,m.x,m.y,m.size*4);
        headGlow.addColorStop(0,"rgba(200,255,220,1)");headGlow.addColorStop(0.3,"rgba(0,255,100,0.8)");headGlow.addColorStop(0.6,"rgba(0,200,50,0.3)");headGlow.addColorStop(1,"rgba(0,100,0,0)");
        ctx.fillStyle=headGlow;ctx.beginPath();ctx.arc(m.x,m.y,m.size*4,0,Math.PI*2);ctx.fill();
        ctx.fillStyle="#fff";ctx.beginPath();ctx.arc(m.x,m.y,m.size,0,Math.PI*2);ctx.fill();
        ctx.restore();
        if(m.y>canvas.height+50||m.x>canvas.width+50)meteors.splice(i,1);
    }
    requestAnimationFrame(draw);
}
draw();

function updateStats(){
    fetch("/stats").then(r=>r.json()).then(d=>{
        document.getElementById("stats").innerText=d.online+" online | "+d.waiting+" search | "+d.chats+" chats";
    });
}
setInterval(updateStats,2000);updateStats();

function showPolicy(){
    document.getElementById("policy-modal").style.display="flex";
}

function agreeAndSearch(){
    document.getElementById("policy-modal").style.display="none";
    document.getElementById("search-btn").style.display="none";
    document.getElementById("searching").style.display="block";
    startSearch();
}

function startSearch(){
    fetch("/search",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({uid:uid})})
    .then(r=>r.json()).then(d=>{
        if(d.error){
            document.getElementById("limit").style.display="block";
            document.getElementById("search-btn").style.display="none";
            document.getElementById("searching").style.display="none";
            setTimeout(()=>{document.getElementById("limit").style.display="none";document.getElementById("search-btn").style.display="block";},3000);
        }else if(d.found){
            localStorage.setItem("chat_id",d.chat_id);
            localStorage.setItem("peer",d.peer);
            window.location.href="/chat";
        }else{
            checkFound();
        }
    });
}

function checkFound(){
    fetch("/check?uid="+uid).then(r=>r.json()).then(d=>{
        if(d.found){localStorage.setItem("chat_id",d.chat_id);localStorage.setItem("peer",d.peer);window.location.href="/chat";}
        else{setTimeout(checkFound,1000);}
    });
}
</script>
</body>
</html>"""

HTML_CHAT = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>Chat</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;width:100%;position:fixed;overflow:hidden}
body{font-family:Arial;background:#0b141a}
#app{display:flex;flex-direction:column;height:100%;max-width:800px;margin:0 auto;width:100%}
#top{background:#202c33;padding:10px 16px;color:white;font-weight:bold;font-size:17px;flex-shrink:0;display:flex;justify-content:space-between;align-items:center}
#msgs{flex:1;overflow-y:auto;padding:5px 16px 10px 16px;display:flex;flex-direction:column;gap:4px}
.m-right{align-self:flex-end;background:#005c4b;color:white;padding:6px 12px;border-radius:8px;max-width:80%;word-wrap:break-word;font-size:15px}
.m-left{align-self:flex-start;background:#202c33;color:white;padding:6px 12px;border-radius:8px;max-width:80%;word-wrap:break-word;font-size:15px}
#ended{display:none;text-align:center;color:white;padding:10px 0;margin-bottom:10px;font-size:18px}
#bottom{background:#202c33;padding:8px;display:flex;gap:6px;align-items:center;flex-shrink:0}
#txt{flex:1;padding:10px 15px;border:none;border-radius:20px;background:#2a3942;color:white;font-size:16px;outline:none}
#send{width:42px;height:42px;border:none;border-radius:50%;background:#00a884;color:white;font-size:20px;cursor:pointer;flex-shrink:0}
#end-btn{background:#d32f2f;color:white;border:none;padding:8px 16px;border-radius:20px;cursor:pointer;font-size:14px}
</style>
</head>
<body>
<div id="app">
<div id="top"><span>Mask 🎭</span><button id="end-btn" onclick="endChat()">❌ Завершить</button></div>
<div id="msgs"></div>
<div id="ended">Чат завершён<br><br><button onclick="goMain()" style="background:#00a884;color:white;border:none;padding:10px 20px;border-radius:20px;font-size:16px;cursor:pointer">🏠 Главное меню</button></div>
<div id="bottom">
<input id="txt" placeholder="Message" maxlength="1000">
<button id="send" onclick="sendMsg()">➤</button>
</div>
</div>
<script>
var uid=localStorage.getItem("uid");
var chat_id=localStorage.getItem("chat_id");
var peer=localStorage.getItem("peer");
var ended=false;

function loadMsgs(){
    if(ended)return;
    fetch("/messages?chat_id="+chat_id).then(r=>r.json()).then(d=>{
        if(d.ended){
            ended=true;
            document.getElementById("ended").style.display="block";
            document.getElementById("bottom").style.display="none";
            document.getElementById("end-btn").style.display="none";
            loadMsgs();return;
        }
        var div=document.getElementById("msgs");
        if(!d.ended)div.innerHTML="";
        d.messages.forEach(m=>{
            var el=document.createElement("div");
            el.className=m.sender===uid?"m-right":"m-left";
            el.innerText=m.text;
            div.appendChild(el);
        });
        div.scrollTop=div.scrollHeight;
    });
}

function sendMsg(){
    if(ended)return;
    var t=document.getElementById("txt").value.trim();
    if(!t||t.length>1000)return;
    fetch("/send_msg",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({chat_id:chat_id,sender:uid,text:t})})
    .then(()=>{document.getElementById("txt").value="";loadMsgs();});
}

function endChat(){
    fetch("/end_chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({chat_id:chat_id})})
    .then(()=>{
        ended=true;
        document.getElementById("ended").style.display="block";
        document.getElementById("bottom").style.display="none";
        document.getElementById("end-btn").style.display="none";
        loadMsgs();
    });
}

function goMain(){
    localStorage.removeItem("chat_id");localStorage.removeItem("peer");
    window.location.href="/";
}
document.getElementById("txt").addEventListener("keydown",function(e){if(e.key==="Enter"){e.preventDefault();sendMsg();}});
loadMsgs();setInterval(loadMsgs,1000);
</script>
</body>
</html>"""

@app.route("/")
def main():
    return render_template_string(HTML_MAIN)

@app.route("/chat")
def chat():
    return render_template_string(HTML_CHAT)

@app.route("/stats")
def stats():
    conn=sqlite3.connect(DB)
    c=conn.cursor()
    c.execute("SELECT COUNT(*) FROM waiting")
    w=c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM chats WHERE active=1")
    ch=c.fetchone()[0]
    conn.close()
    return jsonify({"online":w+ch*2,"waiting":w,"chats":ch})

@app.route("/search",methods=["POST"])
def search():
    data=request.get_json()
    uid=data["uid"]
    conn=sqlite3.connect(DB)
    c=conn.cursor()
    c.execute("SELECT COUNT(*) FROM waiting")
    w=c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM chats WHERE active=1")
    ch=c.fetchone()[0]
    total=w+ch*2
    if total>=300:
        conn.close()
        return jsonify({"error":"limit"})
    c.execute("SELECT user_id FROM waiting WHERE user_id!=? LIMIT 1",(uid,))
    r=c.fetchone()
    if r:
        peer=r[0]
        c.execute("DELETE FROM waiting WHERE user_id=?",(peer,))
        c.execute("DELETE FROM waiting WHERE user_id=?",(uid,))
        c.execute("INSERT INTO chats(user1,user2,active) VALUES(?,?,1)",(uid,peer))
        chat_id=c.lastrowid
        conn.commit()
        conn.close()
        return jsonify({"found":True,"chat_id":chat_id,"peer":peer})
    else:
        c.execute("INSERT OR IGNORE INTO waiting(user_id) VALUES(?)",(uid,))
        conn.commit()
        conn.close()
        return jsonify({"found":False})

@app.route("/check")
def check():
    uid=request.args.get("uid")
    conn=sqlite3.connect(DB)
    c=conn.cursor()
    c.execute("SELECT id FROM chats WHERE (user1=? OR user2=?) AND active=1",(uid,uid))
    r=c.fetchone()
    if r:
        chat_id=r[0]
        c.execute("SELECT user1,user2 FROM chats WHERE id=?",(chat_id,))
        u1,u2=c.fetchone()
        peer=u1 if u2==uid else u2
        conn.close()
        return jsonify({"found":True,"chat_id":chat_id,"peer":peer})
    conn.close()
    return jsonify({"found":False})

@app.route("/messages")
def messages():
    chat_id=request.args.get("chat_id")
    conn=sqlite3.connect(DB)
    c=conn.cursor()
    c.execute("SELECT active FROM chats WHERE id=?",(chat_id,))
    r=c.fetchone()
    if not r or r[0]==0:
        conn.close()
        return jsonify({"ended":True,"messages":[]})
    c.execute("SELECT sender,text,ts FROM messages WHERE chat_id=? ORDER BY id",(chat_id,))
    msgs=[{"sender":x[0],"text":x[1],"ts":x[2]} for x in c.fetchall()]
    conn.close()
    return jsonify({"ended":False,"messages":msgs})

@app.route("/send_msg",methods=["POST"])
def send_msg():
    data=request.get_json()
    conn=sqlite3.connect(DB)
    c=conn.cursor()
    ts=int(time.time())
    c.execute("INSERT INTO messages(chat_id,sender,text,ts) VALUES(?,?,?,?)",(data["chat_id"],data["sender"],data["text"][:1000],ts))
    conn.commit()
    conn.close()
    return jsonify({"ok":True})

@app.route("/end_chat",methods=["POST"])
def end_chat():
    data=request.get_json()
    conn=sqlite3.connect(DB)
    c=conn.cursor()
    c.execute("UPDATE chats SET active=0 WHERE id=?",(data["chat_id"],))
    conn.commit()
    conn.close()
    return jsonify({"ok":True})

if __name__=="__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
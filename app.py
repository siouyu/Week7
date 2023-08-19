from flask import * 
import mysql.connector

def connection():
    con = mysql.connector.connect(
        user = "root",
        password = "test",
        host = "127.0.0.1",
        database = "website",
    )
    return con

app = Flask(__name__)
app.secret_key = "secret"

# 首頁
@app.route("/") 
def home():
    if session.get("username"):
        return redirect("/member")
    else:
        return render_template("home.html")

# 註冊
@app.route("/signup", methods = ["POST"])
def signup():
    name = request.form.get("name")
    username = request.form.get("username")
    password = request.form.get("password")
    try:
        con = connection()
        cursor = con.cursor()
        check = "SELECT username FROM member WHERE username = %s"
        user = (username,) 
        cursor.execute(check, user)
        check_username = cursor.fetchone()
        if check_username != None : 
            return redirect("/error?message=帳號已經被註冊")
        else:
            insert = "INSERT INTO member (name, username, password) VALUES (%s, %s, %s)"
            insert_value = (name, username, password)
            cursor.execute(insert, insert_value)
            con.commit()
            # 註冊後登入
            select = "SELECT id, username FROM member WHERE username = %s"
            select_value = (username,)
            cursor.execute(select, select_value)
            for i in cursor:
                session["userID"] = i[0]
                session["username"] = i[1]
            return redirect("/member")
    except Exception as e:
        return jsonify({"error": e}), 500  # 把錯顯示在前端
    finally:
        con.close()

# 登入
@app.route("/signin", methods = ["POST"]) 
def signin():
    username = request.form.get("username")
    password = request.form.get("password")
    try:
        con = connection()
        cursor = con.cursor()
        check = "SELECT id, password FROM member WHERE username = %s"
        check_value = (username,)
        cursor.execute(check, check_value)
        for member in cursor: 
            if member[1] == password:
                session["userID"] = member[0]
                session["username"] = username
                return redirect("/member")
        return redirect("/error?message=帳號或密碼輸入錯誤")
    except Exception as e:
        return jsonify({"error": e}), 500
    finally:
        con.close()

# 登出
@app.route("/signout")
def signout():
    session.clear()
    return redirect("/")

# 會員頁
@app.route("/member")
def member():
    if session.get("username"): 
        try:
            con = connection()
            cursor = con.cursor()
            check_name = "SELECT name FROM member WHERE username =%s"
            check_value = (session["username"],)
            cursor.execute(check_name, check_value)
            for name in cursor:
                name = name[0]
            # 留言
            content = "SELECT name, content FROM member INNER JOIN message ON member.id=message.member_id ORDER BY message.time DESC"
            cursor.execute(content)
            row = []
            for i in cursor:
                row.append([i[0],i[1]])
            return render_template("member.html", name = name, row = row) # 前面的 row 對 html，後面的 row 是 list
        except Exception as e:
            return jsonify({"error": e}), 500
        finally:
            con.close()
    else:
        return redirect("/")

# 留言系統
@app.route("/createMessage", methods = ["POST"])
def createMessage():
    if session.get("userID"):
        try:
            con = connection()
            cursor = con.cursor()
            message = request.form.get("message")
            insert = "INSERT INTO message (member_id, content) VALUES (%s, %s) "
            insert_value = (session["userID"], message)
            cursor.execute(insert, insert_value)
            con.commit()
            return redirect("/member")
        except Exception as e:
            return jsonify({"error": e}), 500
        finally:
            con.close()
    else:
        return redirect("/")

# 查詢會員資料
@app.route("/api/member", methods = ["GET", "PATCH"])
def api_member():
    if session.get("username"): # 判定會員是否登入
        try:
            con = connection()
            cursor = con.cursor()
            username = request.args.get("username")
            check_user = "SELECT id, name FROM member WHERE username = %s"
            check_value = (username,)
            cursor.execute(check_user, check_value)
            user_data = cursor.fetchone()
            if user_data:
                data = {
                    "data":{
                        "id": user_data[0],
                        "name": user_data[1],
                        "username": username
                    }
                }
                return jsonify(data)
            else:
                data = {
                    "data":null
                }
                return jsonify(data)
        except Exception as e:
            return jsonify({"error": e}), 500
        finally:
            con.close()
    else:
        if session.get("username") and request.methods == "PATCH":
            try:
                con = connection()
                cursor = con.cursor()
                rename = request.get_json()
                change = "UPDATE member SET name = %s WHERE id = %s"
                change_value = (rename["name"], session["userID"])
                cursor.execute(change, change_value)
                con.commit()
                return jsonify({"ok": True})
            except:
                return jsonify({"error": True})
            finally:
                con.close()

# 失敗頁
@app.route("/error")
def error():
    message = request.args.get("message")
    return render_template("error.html", message = message)

if __name__ == "__main__":
    app.run(port = 3000, debug = True)
    app.secret_key = "secret"

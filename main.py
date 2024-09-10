from flask import Flask, render_template, session, redirect, request, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
from string import ascii_uppercase
import random


app = Flask(__name__)
app.config["SECRET_KEY"] = "/Ys34RPDaBcuBRZPSwnKyRp/d3W0MVEqbsHbKtsYnRI="
socketio = SocketIO(app)


rooms = {}  


def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)

        if code not in rooms:
            break

    return code


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name:
            return render_template("home.html", error="Please, Enter Your Name!", code=code, name=name)
        
        if join is not False and not code:
            return render_template("home.html", error="Please, Enter Room Code!", code=code, name=name)

        room = code
        if create is not False:
            room = generate_unique_code(6)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("home.html", error="Invalid Room Code!", code=code, name=name)

        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))
    
    return render_template("home.html")


@app.route("/room", methods=["GET"])
def room():
    room = session.get("room")
    name = session.get("name")
    if room is None or name is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, name=name, messages=rooms[room]["messages"])


@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return 
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")


@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")


@socketio.on("disconnect")
@socketio.on("leave")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]

    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left the room {room}")


if __name__ == "__main__":
    socketio.run(app=app, host="localhost", port=8070, debug=True, use_reloader=True, log_output=True)


# openssl rand -base64 32

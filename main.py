from flask import Flask, render_template, redirect, request, session, flash, url_for
from data import db_session
from data.users import User
from data.news import News
from data.dialogues import Chat
from data.message import Message
from forms.user import RegisterForm, LoginForm, ProfileForm
from forms.chat import MessageForm
from forms.news import NewsForm
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import sqlite3
import requests


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceumproject_messenger_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


def get_weather(city_id):
    appid = "6f50f9148db63842ad3384b3f567518e"
    res = requests.get("http://api.openweathermap.org/data/2.5/weather",
                       params={'id': city_id, 'units': 'metric', 'lang': 'ru', 'APPID': appid})
    data = res.json()
    a = "Погодные условия: " + str(data['weather'][0]['description'])
    b = "Температура: " + str(data['main']['temp'])
    c = "Минимальная температура: " + str(data['main']['temp_min'])
    d = "Максимальная температура: " + str(data['main']['temp_max'])
    return [a, b, c, d]


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/")
@app.route("/mainpage")
def mainpage():
    if current_user.is_authenticated:
        return render_template("mainpage.html", weather=current_user.city_weather,
                               dat=get_weather(current_user.city_id))
    return redirect("/login")


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            surname=form.surname.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        login_user(user)
        return redirect('/')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/mainpage")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/login")


@app.route('/edit_my_profile', methods=['GET', 'POST'])
def edit_profile():
    form = ProfileForm()
    if request.method == "GET":
        if current_user.is_authenticated:
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.id == current_user.id).first()
            form.name.data = user.name
            form.surname.data = user.surname
            form.address.data = user.address
            form.site.data = user.site
            form.birthday.data = user.birthday
            avatar = user.avatar
        else:
            return redirect('/login')
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        user.name = form.name.data
        user.surname = form.surname.data
        user.site = form.site.data
        user.birthday = form.birthday.data
        db_sess.commit()
        return redirect('/my_profile')
    return render_template('edit_my_profile.html', form=form, avatar=avatar,
                           weather=current_user.city_weather, dat=get_weather(current_user.city_id))


@app.route('/my_profile', methods=['GET', 'POST'])
def my_profile():
    if request.method == "GET":
        if current_user.is_authenticated:
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.id == current_user.id).first()
            news = db_sess.query(News).filter(News.user_id == current_user.id)
            return render_template("my_profile.html", user=user, news=news,
                                   weather=current_user.city_weather, dat=get_weather(current_user.city_id))
    if request.method == "POST":
        fileobj = request.files['file']
        if fileobj:
            file_extensions = ["JPG", "JPEG", "PNG", "GIF"]
            uploaded_file_extension = fileobj.filename.split(".")[1]
            # validating file extension
            if uploaded_file_extension.upper() in file_extensions:
                destination_path = f"static/uploads/{fileobj.filename}"
                fileobj.save(destination_path)
                try:
                    conn = sqlite3.connect("db/database.db")
                    cursor = conn.cursor()
                    # inserting data into table usercontent
                    id_ = session['_user_id']
                    cursor.execute(f"""update users set avatar=? where id = ?""", (destination_path, int(id_)))
                    conn.commit()
                    conn.close()
                except sqlite3.Error as error:
                    # using flash function of flask to flash errors.
                    flash(f"{error}")
                    return redirect('/my_profile')
    return redirect("/my_profile")


@app.route("/profile&<int:id_>")
def profile(id_):
    if current_user.is_authenticated:
        if current_user.id == id:
            return redirect('/my_profile')
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == id_).first()
        if not user:
            return redirect('/all_people')
        return render_template("profile.html", user=user,
                               weather=current_user.city_weather, dat=get_weather(current_user.city_id))
    return redirect("/login")


@app.route('/news',  methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        current_user.news.append(news)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('my_profile')
    return render_template('news.html', title='Добавление новости',
                           form=form, weather=current_user.city_weather, dat=get_weather(current_user.city_id))


@app.route('/news&<int:id_>', methods=['GET', 'POST'])
@login_required
def edit_news(id_):
    form = NewsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id_,
                                          News.user == current_user
                                          ).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id_,
                                          News.user == current_user
                                          ).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            db_sess.commit()
            return redirect('/my_profile')
    return render_template('news.html',
                           title='Редактирование новости',
                           form=form,
                           weather=current_user.city_weather, dat=get_weather(current_user.city_id)
                           )


@app.route('/news_delete&<int:id_>', methods=['GET', 'POST'])
@login_required
def news_delete(id_):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id_,
                                      News.user == current_user
                                      ).first()
    if news:
        db_sess.delete(news)
        db_sess.commit()
    return redirect('/my_profile')


@app.route('/dialogues', methods=['GET', 'POST'])
def dialogues():
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        dialogues_ = db_sess.query(Chat).filter(Chat.user1 == current_user.id).all()
        dialogues_ = [int(str(i).split()[-1]) for i in dialogues_]
        users = db_sess.query(User).filter(User.id.in_(dialogues_)).all()
        dialogues_ = db_sess.query(Chat).filter(Chat.user2 == current_user.id).all()
        dialogues_ = [str(i).split()[3] for i in dialogues_]
        users2 = db_sess.query(User).filter(User.id.in_(dialogues_)).all()
        return render_template("dialogues.html", users=users, users2=users2,
                               weather=current_user.city_weather, dat=get_weather(current_user.city_id))
    return redirect("/login")


@app.route('/delete_dialogue&<int:id_>', methods=['GET', 'POST'])
def delete_dialogue(id_):
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        chat = db_sess.query(Chat).filter(Chat.user1 == current_user.id, Chat.user2 == id_).first()
        if not chat:
            chat = db_sess.query(Chat).filter(Chat.user1 == id_, Chat.user2 == current_user.id).first()
        if chat:
            messages = db_sess.query(Message).filter(Message.chat_id).first()
            db_sess.delete(chat)
            if messages:
                db_sess.delete(messages)
            db_sess.commit()
        return redirect("/dialogues")
    return redirect("/login")


@app.route('/dialogue&<int:id_>', methods=['GET', 'POST'])
def dialogue_(id_):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == id_).first()
    if current_user.is_authenticated:
        if current_user.id != id_ and user:
            form = MessageForm()
            dialogue = db_sess.query(Chat).filter(Chat.user1 == current_user.id, Chat.user2 == id_).first()
            if not dialogue:
                dialogue = db_sess.query(Chat).filter(Chat.user1 == id_, Chat.user2 == current_user.id).first()
            if not dialogue:
                chat = Chat(
                    user1=current_user.id,
                    user2=id_
                )
                db_sess.add(chat)
                db_sess.commit()
                dialogue = chat
            messages = db_sess.query(Message).filter(Message.chat_id == dialogue.chat_id)
            if form.validate_on_submit():
                db_sess = db_session.create_session()
                message = Message(
                    chat_id=dialogue.chat_id,
                    user_id=current_user.id,
                    content=form.message.data
                )
                db_sess.add(message)
                db_sess.commit()
                return redirect(f'/dialogue&{id_}')
            return render_template("message.html", messages=messages, user=user,
                                   form=form, weather=current_user.city_weather, dat=get_weather(current_user.city_id))
        return redirect("/dialogues")
    return redirect("/login")


@app.route('/all_people', methods=['GET', 'POST'])
def all_people():
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        users = db_sess.query(User).filter(User.id != current_user.id).all()
        return render_template("all_people.html", users=users,
                               weather=current_user.city_weather, dat=get_weather(current_user.city_id))
    return redirect("/login")


@app.route("/music", methods=['GET', 'POST'])
def music():
    if request.method == "GET":
        conn = sqlite3.connect("db/database.db")
        cursor = conn.cursor()
        songs = cursor.execute(f"""select music from musics where id = {int(session['_user_id'])}""").fetchall()
        conn.close()
        return render_template('music.html', songs=songs,
                               weather=current_user.city_weather, dat=get_weather(current_user.city_id))
    if request.method == "POST":
        fileobj = request.files['file']
        file_extensions = ["MPEG", "MP3", "MOV", "AVI"]
        uploaded_file_extension = fileobj.filename.split(".")[1]
        # validating file extension
        if uploaded_file_extension.upper() in file_extensions:
            destination_path = fileobj.filename
            fileobj.save(f"static/music/{fileobj.filename}")
            try:
                conn = sqlite3.connect("db/database.db")
                cursor = conn.cursor()
                # inserting data into table usercontent
                id_ = session['_user_id']
                cursor.execute(f"""insert into musics (id, music) values (?, ?)""", (int(id_), destination_path))
                conn.commit()
                conn.close()
            except sqlite3.Error as error:
                # using flash function of flask to flash errors.
                flash(f"{error}")
                return redirect('/music')
        else:
            flash("only music are accepted")
    return redirect(url_for("music"))


@app.route('/weather', methods=['GET', 'POST'])
def weather():
    if request.method == "GET":
        return render_template('weather.html', weather=current_user.city_weather, dat=get_weather(current_user.city_id))
    if request.method == "POST":
        s_city = request.form['name']
        appid = "6f50f9148db63842ad3384b3f567518e"
        try:
            res = requests.get("http://api.openweathermap.org/data/2.5/find",
                               params={'q': s_city, 'type': 'like', 'units': 'metric', 'APPID': appid})
            data = res.json()
            city_id = data['list'][0]['id']
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.id == current_user.id).first()
            user.city_weather = s_city
            user.city_id = city_id
            db_sess.commit()
        except Exception as e:
            message = 'Неизвестный город'
            return render_template('weather.html', message=message,
                                   weather=current_user.city_weather, dat=get_weather(current_user.city_id))
    return redirect('/mainpage')


def main():
    db_session.global_init("db/database.db")
    app.run(port=8080, host='127.0.0.1')


if __name__ == '__main__':
    main()

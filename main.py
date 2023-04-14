from flask import Flask, render_template, redirect, request, session, flash, url_for
from data import db_session
from data.users import User
from data.news import News
from forms.user import RegisterForm, LoginForm, ProfileForm
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import sqlite3


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/")
@app.route("/mainpage")
def mainpage():
    if current_user.is_authenticated:
        return render_template("mainpage.html")
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
            form.email.data = user.email
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
        user.address = form.address.data
        user.email = form.email.data
        user.site = form.site.data
        user.birthday = form.birthday.data
        db_sess.commit()
        return redirect('/my_profile')
    return render_template('edit_my_profile.html', form=form, avatar=avatar)


@app.route('/my_profile', methods=['GET', 'POST'])
def my_profile():
    if request.method == "GET":
        if current_user.is_authenticated:
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.id == current_user.id).first()
            news = db_sess.query(News).filter(News.user_id == current_user.id)
            return render_template("my_profile.html", user=user, news=news)
    print(request.method)
    if request.method == "POST":
        estination_path = ""
        fileobj = request.files['file']
        if fileobj:
            file_extensions = ["JPG", "JPEG", "PNG", "GIF"]
            uploaded_file_extension = fileobj.filename.split(".")[1]
            # validating file extension
            if (uploaded_file_extension.upper() in file_extensions):
                destination_path = f"static/uploads/{fileobj.filename}"
                fileobj.save(destination_path)
                try:
                    conn = sqlite3.connect("db/database.db")
                    cursor = conn.cursor()
                    # inserting data into table usercontent
                    id = session['_user_id']
                    cursor.execute(f"""update users set avatar=? where id = ?""", (destination_path, int(id)))
                    conn.commit()
                    conn.close()
                except sqlite3.Error as error:
                    # using flash function of flask to flash errors.
                    flash(f"{error}")
                    return redirect('/my_profile')
    return redirect("/my_profile")


@app.route("/profile&<int:id>")
def profile(id):
    if current_user.is_authenticated:
        if current_user.id == id:
            return redirect('/my_profile')
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == id).first()
        return render_template("profile.html", user=user)
    return redirect("/login")


def main():
    db_session.global_init("db/database.db")
    app.run(port=8080, host='127.0.0.1')


if __name__ == '__main__':
    main()
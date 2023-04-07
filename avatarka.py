from flask import Flask, request, render_template, redirect, make_response, url_for, flash

from werkzeug.utils import secure_filename

import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
global i
conn = sqlite3.connect("db/base.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("""select * from photos""")
rows = cursor.fetchall()
i = len(rows) + 1


@app.route("/upload", methods=['POST', 'GET'])
def upload():
    if request.method == "GET":
        return render_template('home.html')
    elif request.method == "POST":
        destination_path = ""
        fileobj = request.files['file']
        file_extensions = ["JPG", "JPEG", "PNG", "GIF"]
        uploaded_file_extension = fileobj.filename.split(".")[1]
        # validating file extension
        if (uploaded_file_extension.upper() in file_extensions):
            destination_path = f"static/uploads/{fileobj.filename}"
            fileobj.save(destination_path)
            try:
                conn = sqlite3.connect("db/base.db")
                cursor = conn.cursor()
                # inserting data into table usercontent
                global i
                print(i)
                cursor.execute("""insert into photos values(:id, :photo)""",
                               {'id': i, 'photo': destination_path})
                i += 1
                print(i)
                conn.commit()
                conn.close()
            except sqlite3.Error as error:
                # using flash function of flask to flash errors.
                flash(f"{error}")
                return render_template('home.html')
        else:
            flash("only images are accepted")
            return render_template('home.html')
    return redirect(url_for("view"))


@app.route("/view")
def view():

    try:
        conn = sqlite3.connect("db/base.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""select * from photos""")
        rows = cursor.fetchall()
        print(rows)
        conn.close()
    except sqlite3.Error as error:
        flash("Something went wrong while uploading file to database!")
        return render_template('home.html')
    return render_template('view.html', response=rows)


app.run(port=8080, host='127.0.0.1')
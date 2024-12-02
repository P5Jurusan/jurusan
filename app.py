from flask import Flask, render_template, request, redirect, url_for, flash, session
import secrets
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Konfigurasi Database SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jurusan.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    nip = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

def init_db():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nip = request.form.get('nip')
        password = request.form.get('password')
        
        #validasi
        if not nip or not nip.isdigit() or len(nip) != 18:
            flash('NIP harus terdiri dari 18 angka!', 'danger')
            return redirect(url_for('login'))
        
        if not password or len(password) < 8:
            flash('Password harus terdiri dari minimal 8 karakter!', 'danger')
            return redirect(url_for('login'))

        # Cek NIP dan Password
        user = User.query.filter_by(nip=nip, password=password).first()
        if user:
            session['user'] = user.name
            flash('Login berhasil!', 'success')
            return redirect(url_for('index'))
        else:
            flash('NIP atau password salah!', 'danger')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        nip = request.form.get('nip')
        name = request.form.get('name')
        password = request.form.get('password')
        
        #validasi
        if not nip or not nip.isdigit() or len(nip) != 18:
            flash('NIP harus terdiri dari 18 angka!', 'danger')
            return redirect(url_for('register'))
        
        if not password or len(password) < 8:
            flash('Password harus terdiri dari minimal 8 karakter!', 'danger')
            return redirect(url_for('register'))

        # Simpan data ke database
        new_user = User(nip=nip, name=name, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registrasi berhasil!', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)

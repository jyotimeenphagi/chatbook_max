from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Production में env variable में डालें
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

# ------------------ Models ------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    photos = db.relationship('Photo', backref='owner', lazy=True)

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    caption = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# ------------------ Routes ------------------

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('profile'))
    return redirect(url_for('login'))

# -------- Signup --------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        if User.query.filter_by(email=email).first():
            flash("Email already registered!")
            return redirect(url_for('signup'))
        
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        flash("Account created! Please login.")
        return redirect(url_for('login'))
    return render_template('signup.html')

# -------- Login --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('profile'))
        flash("Invalid credentials!")
        return redirect(url_for('login'))
    return render_template('login.html')

# -------- Logout --------
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out successfully!")
    return redirect(url_for('login'))

# -------- Profile --------
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    photos = user.photos
    return render_template('profile.html', user=user, photos=photos)

# -------- Upload Photo --------
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file selected!")
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash("File name is empty!")
            return redirect(request.url)

        # User-specific folder
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], user.username)
        os.makedirs(user_folder, exist_ok=True)

        filepath = os.path.join(user_folder, file.filename)
        file.save(filepath)

        caption = request.form.get('caption')
        new_photo = Photo(filename=file.filename, caption=caption, owner=user)
        db.session.add(new_photo)
        db.session.commit()

        flash("Photo uploaded!")
        return redirect(url_for('profile'))

    return render_template('upload.html')

# ------------------ Run App ------------------
if __name__ == "__main__":
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, has_request_context, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, EmailField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import json
from collections import defaultdict
import calendar
import random

# Message definitions
MESSAGES = {
    'username_exists': 'Бұл пайдаланушы аты бос емес',
    'email_exists': 'Бұл email бос емес',
    'passwords_dont_match': 'Құпия сөздер сәйкес келмейді',
    'register_success': 'Тіркелу сәтті аяқталды! Енді жүйеге кіруіңізге болады',
    'login_success': 'Жүйеге сәтті кірдіңіз!',
    'invalid_credentials': 'Қате пайдаланушы аты немесе құпия сөз',
    'logout_success': 'Жүйеден сәтті шықтыңыз',
    'program_created': 'Жаттығу бағдарламасы сәтті құрылды',
    'file_not_allowed': 'Бұл файл түріне рұқсат етілмеген'
}

# Form Classes
class LoginForm(FlaskForm):
    username = StringField('Пайдаланушы аты', validators=[DataRequired()])
    password = PasswordField('Құпия сөз', validators=[DataRequired()])
    remember = BooleanField('Мені есте сақтау')
    submit = SubmitField('Кіру')

class RegistrationForm(FlaskForm):
    username = StringField('Пайдаланушы аты', validators=[DataRequired(), Length(min=4, max=20)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Құпия сөз', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Құпия сөзді растау', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Тіркелу')

class ProgramForm(FlaskForm):
    title = StringField('Бағдарлама атауы', validators=[DataRequired()])
    description = StringField('Сипаттама')
    category = StringField('Санат')
    difficulty = StringField('Қиындық деңгейі')
    duration = StringField('Ұзақтығы')
    image = StringField('Сурет')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fitness.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm'}

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Association table for shared programs
program_shares = db.Table('program_shares',
    db.Column('program_id', db.Integer, db.ForeignKey('workout_program.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

# Add muscle group translations
MUSCLE_GROUP_TRANSLATIONS = {
    'Chest': 'Кеуде',
    'Back': 'Арқа',
    'Shoulders': 'Иық',
    'Legs': 'Аяқ',
    'Biceps': 'Бицепс',
    'Triceps': 'Трицепс'
}

DIFFICULTY_TRANSLATIONS = {
    'Beginner': 'Бастауыш',
    'Intermediate': 'Орташа',
    'Advanced': 'Жоғары'
}

EQUIPMENT_TRANSLATIONS = {
    'Barbell': 'Штанга',
    'Pull-up Bar': 'Турник',
    'Bench': 'Орындық',
    'Cable Machine': 'Блок құрылғысы',
    'Dumbbells': 'Гантельдер'
}

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    workout_programs = db.relationship('WorkoutProgram', backref='user', lazy=True)
    completed_workouts = db.relationship('CompletedWorkout', backref='user', lazy=True)
    achievements = db.relationship('Achievement', backref='user', lazy=True)
    goals = db.relationship('Goal', backref='user', lazy=True)
    shared_programs = db.relationship('WorkoutProgram', secondary=program_shares, lazy='subquery',
                                     backref=db.backref('shared_with', lazy=True))
    saved_programs = db.relationship('WorkoutProgram', secondary=program_shares, lazy='subquery',
                                     backref=db.backref('saved_with', lazy=True))

class WorkoutProgram(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    exercises = db.Column(db.Text)  # JSON format for structured exercise data
    category = db.Column(db.String(50), nullable=False, default='General')
    image_filename = db.Column(db.String(255))
    difficulty = db.Column(db.String(20), nullable=False, default='Medium')
    duration = db.Column(db.Integer)  # Duration in weeks
    is_public = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    completed_workouts = db.relationship('CompletedWorkout', backref='program', lazy=True)
    exercise_videos = db.relationship('ExerciseVideo', backref='program', lazy=True)
    target_muscle_groups = db.Column(db.String(200))  # Comma-separated muscle groups
    equipment_needed = db.Column(db.String(200))  # Comma-separated equipment list
    workout_frequency = db.Column(db.String(50))  # e.g., "3x5", "5x5", "Daily"
    fitness_level = db.Column(db.String(20))  # Beginner, Intermediate, Advanced
    program_type = db.Column(db.String(50))  # Strength, Bodybuilding, Toning, etc.
    calories_burn = db.Column(db.Integer)  # Estimated calories burned per session

class ExerciseVideo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exercise_name = db.Column(db.String(100), nullable=False)
    video_filename = db.Column(db.String(255))
    program_id = db.Column(db.Integer, db.ForeignKey('workout_program.id'), nullable=False)

class CompletedWorkout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.Text)
    rating = db.Column(db.Integer)  # 1-5 rating
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('workout_program.id'), nullable=False)

class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_earned = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    target_date = db.Column(db.DateTime)
    is_completed = db.Column(db.Boolean, default=False)
    progress = db.Column(db.Integer, default=0)  # 0-100
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False, default='General')
    target_value = db.Column(db.Float)  # For numeric goals (e.g., weight, distance)
    current_value = db.Column(db.Float)  # Current value for numeric goals
    unit = db.Column(db.String(20))  # Unit of measurement (kg, km, etc.)
    frequency = db.Column(db.String(50))  # How often to work on the goal (daily, weekly, etc.)
    priority = db.Column(db.Integer, default=1)  # 1-5 priority level

class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_kz = db.Column(db.String(100))  # Kazakh name
    description = db.Column(db.Text)
    description_kz = db.Column(db.Text)  # Kazakh description
    muscle_group = db.Column(db.String(50), nullable=False)
    muscle_group_kz = db.Column(db.String(50))  # Kazakh muscle group
    secondary_muscles = db.Column(db.String(200))
    secondary_muscles_kz = db.Column(db.String(200))  # Kazakh secondary muscles
    equipment = db.Column(db.String(100))
    equipment_kz = db.Column(db.String(100))  # Kazakh equipment
    difficulty = db.Column(db.String(20))
    difficulty_kz = db.Column(db.String(20))  # Kazakh difficulty
    instructions = db.Column(db.Text)
    instructions_kz = db.Column(db.Text)  # Kazakh instructions
    video_url = db.Column(db.String(255))
    image_filename = db.Column(db.String(255))
    is_public = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        programs = WorkoutProgram.query.filter(
            (WorkoutProgram.is_public == True) | 
            (WorkoutProgram.user_id == current_user.id)
        ).all()
        return render_template('index.html', programs=programs)
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash(MESSAGES['username_exists'], 'danger')
            return render_template('register.html', form=form)
        
        if User.query.filter_by(email=form.email.data).first():
            flash(MESSAGES['email_exists'], 'danger')
            return render_template('register.html', form=form)
        
        if form.password.data != form.confirm_password.data:
            flash(MESSAGES['passwords_dont_match'], 'danger')
            return render_template('register.html', form=form)
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()
        
        flash(MESSAGES['register_success'], 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            flash(MESSAGES['login_success'], 'success')
            return redirect(url_for('index'))
        flash(MESSAGES['invalid_credentials'], 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(MESSAGES['logout_success'], 'success')
    return redirect(url_for('index'))

@app.route('/create_program', methods=['GET', 'POST'])
@login_required
def create_program():
    if request.method == 'POST':
        program = WorkoutProgram(
            title=request.form['title'],
            description=request.form['description'],
            program_type=request.form['program_type'],
            difficulty=request.form['difficulty'],
            duration=int(request.form['duration']),
            workout_frequency=request.form['workout_frequency'],
            user_id=current_user.id
        )
        db.session.add(program)
        db.session.commit()
        flash('Бағдарлама сәтті құрылды!', 'success')
        return redirect(url_for('programs'))
    return render_template('create_program.html')

@app.route('/edit_program/<int:program_id>', methods=['GET', 'POST'])
@login_required
def edit_program(program_id):
    program = WorkoutProgram.query.get_or_404(program_id)
    if program.user_id != current_user.id:
        flash('You do not have permission to edit this program')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        program.title = request.form.get('title')
        program.description = request.form.get('description')
        program.exercises = request.form.get('exercises')
        program.category = request.form.get('category')
        db.session.commit()
        return redirect(url_for('index'))
    
    return render_template('edit_program.html', program=program)

@app.route('/delete_program/<int:program_id>', methods=['POST'])
@login_required
def delete_program(program_id):
    program = WorkoutProgram.query.get_or_404(program_id)
    if program.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Рұқсат етілмеген'}), 403
    
    db.session.delete(program)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/complete_workout/<int:program_id>', methods=['POST'])
@login_required
def complete_workout(program_id):
    program = WorkoutProgram.query.get_or_404(program_id)
    if program.user_id != current_user.id:
        flash('You do not have permission to complete this workout')
        return redirect(url_for('index'))
    
    notes = request.form.get('notes', '')
    completed = CompletedWorkout(
        user_id=current_user.id,
        program_id=program_id,
        notes=notes
    )
    db.session.add(completed)
    db.session.commit()
    return redirect(url_for('index'))

def calculate_streak(user_id):
    """Calculate current and best workout streaks."""
    workouts = CompletedWorkout.query.filter_by(user_id=user_id).order_by(CompletedWorkout.date.desc()).all()
    if not workouts:
        return 0, 0
    
    current_streak = 0
    best_streak = 0
    temp_streak = 0
    today = datetime.now().date()
    last_date = None
    
    for workout in workouts:
        workout_date = workout.date.date()
        if last_date is None:
            if (today - workout_date).days <= 1:
                temp_streak = 1
        else:
            if (last_date - workout_date).days == 1:
                temp_streak += 1
            else:
                if temp_streak > best_streak:
                    best_streak = temp_streak
                temp_streak = 1
        last_date = workout_date
    
    current_streak = temp_streak if last_date and (today - last_date).days <= 1 else 0
    best_streak = max(best_streak, temp_streak)
    
    return current_streak, best_streak

def get_monthly_stats(user_id):
    """Get workout statistics for the current month."""
    start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_date = (start_date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
    
    workouts = CompletedWorkout.query.filter(
        CompletedWorkout.user_id == user_id,
        CompletedWorkout.date.between(start_date, end_date)
    ).all()
    
    total_duration = sum(workout.duration for workout in workouts if workout.duration)
    total_calories = sum(workout.calories_burn for workout in workouts if workout.calories_burn)
    
    return {
        'total_duration': total_duration,
        'total_calories': total_calories,
        'total_workouts': len(workouts)
    }

def get_weekly_activity(user_id):
    """Get workout durations for the last 7 days."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=6)
    
    workouts = CompletedWorkout.query.filter(
        CompletedWorkout.user_id == user_id,
        CompletedWorkout.date.between(start_date, end_date)
    ).all()
    
    daily_duration = defaultdict(int)
    for workout in workouts:
        daily_duration[workout.date.strftime('%a')] += workout.duration if workout.duration else 0
    
    days = [(end_date - timedelta(days=i)).strftime('%a') for i in range(6, -1, -1)]
    return [daily_duration[day] for day in days]

def get_workout_types_distribution(user_id):
    """Get distribution of workout types."""
    workouts = CompletedWorkout.query.filter_by(user_id=user_id).all()
    type_counts = defaultdict(int)
    
    for workout in workouts:
        type_counts[workout.category] += 1
    
    total = sum(type_counts.values())
    if total == 0:
        return [], []
    
    labels = list(type_counts.keys())
    data = [round((count / total) * 100) for count in type_counts.values()]
    
    return labels, data

def get_most_used_exercises(user_id):
    """Get statistics for most frequently used exercises."""
    workouts = CompletedWorkout.query.filter_by(user_id=user_id).all()
    exercise_stats = defaultdict(lambda: {'sets': 0, 'max_weight': 0, 'name': '', 'progress': 0})
    
    for workout in workouts:
        for exercise in workout.exercises:
            stats = exercise_stats[exercise]
            stats['name'] = exercise
            stats['sets'] += 1
            stats['max_weight'] = max(stats['max_weight'], workout.rating or 0)
            stats['image'] = f"{exercise.lower().replace(' ', '-')}.svg"
            
            # Calculate progress based on rating improvement
            initial_rating = CompletedWorkout.query.filter_by(
                user_id=user_id, 
                program_id=workout.program_id,
                rating=workout.rating
            ).order_by(CompletedWorkout.date).first()
            
            if initial_rating and initial_rating.rating:
                progress = ((workout.rating or 0) - initial_rating.rating) / 5 * 100
                stats['progress'] = min(max(round(progress), 0), 100)
    
    # Sort by total sets and get top 5
    sorted_exercises = sorted(
        [{'id': k, **v} for k, v in exercise_stats.items()],
        key=lambda x: x['sets'],
        reverse=True
    )[:5]
    
    return sorted_exercises

@app.route('/stats')
@login_required
def stats():
    current_streak, best_streak = calculate_streak(current_user.id)
    monthly_stats = get_monthly_stats(current_user.id)
    weekly_activity = get_weekly_activity(current_user.id)
    workout_types_labels, workout_types_data = get_workout_types_distribution(current_user.id)
    most_used_exercises = get_most_used_exercises(current_user.id)
    
    return render_template('stats.html',
        total_workouts=monthly_stats['total_workouts'],
        current_streak=current_streak,
        best_streak=best_streak,
        total_hours=round(monthly_stats['total_duration'] / 60, 1),
        calories=monthly_stats['total_calories'],
        weekly_activity=weekly_activity,
        workout_types_labels=workout_types_labels,
        workout_types_data=workout_types_data,
        most_used_exercises=most_used_exercises
    )

@app.route('/upload_image/<int:program_id>', methods=['POST'])
@login_required
def upload_image(program_id):
    program = WorkoutProgram.query.get_or_404(program_id)
    if program.user_id != current_user.id:
        flash('You do not have permission to edit this program')
        return redirect(url_for('index'))
    
    if 'image' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['image']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        program.image_filename = filename
        db.session.commit()
        flash('Image uploaded successfully')
    
    return redirect(url_for('edit_program', program_id=program_id))

@app.route('/calendar')
@login_required
def calendar():
    workouts = CompletedWorkout.query.filter_by(user_id=current_user.id).all()
    workout_dates = {workout.date.date().isoformat(): workout.program.title for workout in workouts}
    return render_template('calendar.html', workout_dates=workout_dates)

@app.route('/achievements')
def achievements():
    # Получаем список разблокированных достижений пользователя
    unlocked = ['first_workout']  # Это пример, в реальности нужно получать из БД
    
    # Общее количество достижений
    total_count = 3  # У нас 3 достижения: first_workout, ten_workouts, workout_master
    
    # Количество разблокированных достижений
    unlocked_count = len(unlocked)
    
    return render_template('achievements.html',
                         unlocked=unlocked,
                         total_count=total_count,
                         unlocked_count=unlocked_count)

def check_achievements(user):
    """Check and award achievements for the user."""
    # Get user statistics
    completed_workouts = CompletedWorkout.query.filter_by(user_id=user.id).count()
    current_streak, best_streak = calculate_streak(user.id)
    
    # Achievement definitions
    achievements = [
        {
            'name': 'Бірінші қадам',  # First Step
            'description': 'Алғашқы жаттығуды аяқтадыңыз',  # Completed your first workout
            'icon': 'first-workout.svg',
            'condition': completed_workouts >= 1
        },
        {
            'name': 'Апта жауынгері',  # Week Warrior
            'description': '7 күн қатарынан жаттығу',  # 7-day workout streak
            'icon': 'streak-7.svg',
            'condition': current_streak >= 7
        },
        {
            'name': 'Жаттығу шебері',  # Workout Master
            'description': '30 жаттығуды аяқтадыңыз',  # Completed 30 workouts
            'icon': 'workout-master.svg',
            'condition': completed_workouts >= 30
        },
        {
            'name': 'Күшті жауынгер',  # Strong Warrior
            'description': '14 күн қатарынан жаттығу',  # 14-day workout streak
            'icon': 'streak-14.svg',
            'condition': current_streak >= 14
        },
        {
            'name': 'Алтын жауынгер',  # Golden Warrior
            'description': '30 күн қатарынан жаттығу',  # 30-day workout streak
            'icon': 'streak-30.svg',
            'condition': current_streak >= 30
        },
        {
            'name': 'Жаттығу фанаты',  # Workout Enthusiast
            'description': '100 жаттығуды аяқтадыңыз',  # Completed 100 workouts
            'icon': 'workout-100.svg',
            'condition': completed_workouts >= 100
        }
    ]
    
    # Check and award achievements
    for achievement_data in achievements:
        # Check if user already has this achievement
        existing_achievement = Achievement.query.filter_by(
            user_id=user.id,
            name=achievement_data['name']
        ).first()
        
        # If achievement condition is met and user doesn't have it yet
        if achievement_data['condition'] and not existing_achievement:
            new_achievement = Achievement(
                name=achievement_data['name'],
                description=achievement_data['description'],
                icon=achievement_data['icon'],
                user_id=user.id
            )
            db.session.add(new_achievement)
            flash(f'Жаңа жетістік алдыңыз: {achievement_data["name"]}!', 'success')
    
    db.session.commit()

@app.route('/start_program/<int:program_id>')
@login_required
def start_program(program_id):
    program = WorkoutProgram.query.get_or_404(program_id)
    
    # Создаем запись о начале программы
    start_date = datetime.utcnow()
    session['program_start'] = {
        'id': program_id,
        'date': start_date.strftime('%Y-%m-%d'),
        'day': 1
    }
    
    flash('Бағдарлама сәтті басталды! Бірінші күнді бастауға дайынсыз ба?', 'success')
    return redirect(url_for('view_workout_day', program_id=program_id, day=1))

@app.route('/workout_day/<int:program_id>/<int:day>')
@login_required
def view_workout_day(program_id, day):
    program = WorkoutProgram.query.get_or_404(program_id)
    
    try:
        exercises_data = json.loads(program.exercises)
        day_key = f"Күн {day}"
        day_exercises = exercises_data.get(day_key, [])
        
        return render_template('workout_day.html',
                             program=program,
                             day=day,
                             exercises=day_exercises,
                             total_days=len(exercises_data))
    except (json.JSONDecodeError, KeyError):
        flash('Жаттығу күні табылмады', 'error')
        return redirect(url_for('view_program', program_id=program_id))

@app.route('/save_for_later/<int:program_id>')
@login_required
def save_for_later(program_id):
    program = WorkoutProgram.query.get_or_404(program_id)
    if program not in current_user.saved_programs:
        current_user.saved_programs.append(program)
        db.session.commit()
        flash('Бағдарлама сақталды!', 'success')
    return redirect(url_for('view_program', program_id=program_id))

@app.route('/share_program/<int:program_id>', methods=['POST'])
@login_required
def share_program(program_id):
    program = WorkoutProgram.query.get_or_404(program_id)
    username = request.form.get('username')
    
    if not username:
        flash('Пайдаланушы атын енгізіңіз', 'danger')
        return redirect(url_for('view_program', program_id=program_id))
    
    user = User.query.filter_by(username=username).first()
    if not user:
        flash('Пайдаланушы табылмады', 'danger')
        return redirect(url_for('view_program', program_id=program_id))
    
    if program in user.shared_programs:
        flash('Бағдарлама бұл пайдаланушымен бұрыннан бөлісілген', 'warning')
        return redirect(url_for('view_program', program_id=program_id))
    
    user.shared_programs.append(program)
    db.session.commit()
    flash(f'Бағдарлама {username} пайдаланушысымен бөлісілді', 'success')
    return redirect(url_for('view_program', program_id=program_id))

@app.route('/goals')
@login_required
def goals():
    active_goals = Goal.query.filter_by(
        user_id=current_user.id,
        is_completed=False
    ).all()
    completed_goals = Goal.query.filter_by(
        user_id=current_user.id,
        is_completed=True
    ).all()
    return render_template('goals.html', 
                         active_goals=active_goals,
                         completed_goals=completed_goals)

@app.route('/create_goal', methods=['GET', 'POST'])
@login_required
def create_goal():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        target_date_str = request.form.get('target_date')
        
        if not target_date_str:
            if is_xhr():
                return jsonify({'success': False, 'message': 'Мақсат күнін көрсету міндетті'})
            flash('Мақсат күнін көрсету міндетті', 'error')
            return redirect(url_for('create_goal'))
            
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
        except ValueError:
            if is_xhr():
                return jsonify({'success': False, 'message': 'Жарамсыз күн пішімі. ЖЖЖЖ-АА-КК пішімін пайдаланыңыз'})
            flash('Жарамсыз күн пішімі. ЖЖЖЖ-АА-КК пішімін пайдаланыңыз', 'error')
            return redirect(url_for('create_goal'))
            
        category = request.form.get('category')
        priority = int(request.form.get('priority'))
        frequency = request.form.get('frequency')
        target_value = request.form.get('target_value')
        unit = request.form.get('unit')
        progress = int(request.form.get('progress', 0))
        
        goal = Goal(
            title=title,
            description=description,
            target_date=target_date,
            category=category,
            priority=priority,
            frequency=frequency,
            target_value=float(target_value) if target_value else None,
            unit=unit if unit else None,
            current_value=float(target_value) * (progress / 100) if target_value else None,
            progress=progress,
            user_id=current_user.id
        )
        db.session.add(goal)
        db.session.commit()

        if is_xhr():
            return jsonify({'success': True, 'message': 'Мақсат сәтті құрылды!'})
        flash('Мақсат сәтті құрылды!', 'success')
        return redirect(url_for('goals'))

    return render_template('create_goal.html')

@app.route('/update_goal_progress/<int:goal_id>', methods=['POST'])
@login_required
def update_goal_progress(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    if goal.user_id != current_user.id:
        if is_xhr():
            return jsonify({'success': False, 'message': 'Бұл мақсатты өзгертуге рұқсатыңыз жоқ'})
        flash('Бұл мақсатты өзгертуге рұқсатыңыз жоқ', 'danger')
        return redirect(url_for('goals'))
    
    if request.is_json:
        data = request.get_json()
        progress = data.get('progress', 0)
    else:
        progress = request.form.get('progress', 0)
    
    try:
        progress = int(progress)
        if not 0 <= progress <= 100:
            raise ValueError
    except ValueError:
        if is_xhr():
            return jsonify({'success': False, 'message': 'Прогресс 0-100 аралығында болуы керек'})
        flash('Прогресс 0-100 аралығында болуы керек', 'danger')
        return redirect(url_for('goals'))
    
    goal.progress = progress
    goal.is_completed = (progress == 100)
    db.session.commit()
    
    if is_xhr():
        return jsonify({
            'success': True, 
            'message': 'Мақсат прогресі сәтті жаңартылды',
            'progress': progress,
            'is_completed': goal.is_completed
        })
    
    flash('Мақсат прогресі сәтті жаңартылды', 'success')
    return redirect(url_for('goals'))

@app.route('/programs')
def programs():
    # Получаем параметры фильтрации
    program_type = request.args.get('program_type')
    level = request.args.get('level')
    duration = request.args.get('duration')

    # Базовый запрос
    query = WorkoutProgram.query.filter(
        (WorkoutProgram.is_public == True) | 
        (WorkoutProgram.user_id == current_user.id if current_user.is_authenticated else False)
    )

    # Применяем фильтры
    if program_type:
        query = query.filter_by(program_type=program_type)
    if level:
        query = query.filter_by(difficulty=level)
    if duration:
        query = query.filter_by(duration=int(duration))

    # Получаем программы
    programs = query.all()

    return render_template('programs.html', programs=programs)

@app.route('/view_program/<int:program_id>')
def view_program(program_id):
    program = WorkoutProgram.query.get_or_404(program_id)
    
    # Get exercises by days
    day_exercises = {}
    if program.exercises:
        try:
            exercises_data = json.loads(program.exercises)
            for day, exercises in exercises_data.items():
                # Handle both numeric and text day formats
                try:
                    if 'Күн' in day:  # If day is in format "Күн X"
                        day_num = int(''.join(filter(str.isdigit, day)))
                    elif 'День' in day:  # If day is in format "День X"
                        day_num = int(''.join(filter(str.isdigit, day)))
                    else:  # If it's just a number or other format
                        day_num = len(day_exercises) + 1
                    day_exercises[day_num] = exercises
                except (ValueError, TypeError):
                    # If we can't parse the day number, use sequential numbering
                    day_num = len(day_exercises) + 1
                    day_exercises[day_num] = exercises
        except json.JSONDecodeError:
            flash('Жаттығуларды жүктеу кезінде қате орын алды', 'error')
    
    return render_template('view_workout_program.html',
                         program=program,
                         day_exercises=day_exercises)

@app.template_filter('from_json')
def from_json(value):
    try:
        return json.loads(value) if value else {}
    except:
        return {}

@app.template_filter('nl2br')
def nl2br(value):
    """Convert newlines to HTML line breaks."""
    if not value:
        return value
    return value.replace('\n', '<br>')

# Add some predefined workout programs
def add_sample_programs():
    with app.app_context():
        # Check if we already have sample programs
        if WorkoutProgram.query.filter_by(title='6 айлық бодибилдинг бағдарламасы').first():
            return

        # Create a system user for predefined programs if not exists
        system_user = User.query.filter_by(username='system').first()
        if not system_user:
            system_user = User(
                username='system',
                email='system@fitness.local',
                password_hash=generate_password_hash('system_password')
            )
            db.session.add(system_user)
            db.session.commit()

        # Sample programs
        programs = [
            {
                'title': '6 айлық бодибилдинг бағдарламасы',
                'description': 'Бұлшықет өсуі мен күш дамытуға арналған толық дене трансформация бағдарламасы.',
                'program_type': 'Бодибилдинг',
                'fitness_level': 'Орташа',
                'duration': 24,
                'workout_frequency': 'Аптасына 5 күн',
                'equipment_needed': 'Толық жабдықталған спортзал',
                'calories_burn': 500,
                'is_public': True,
                'target_muscle_groups': 'Кеуде, Арқа, Иық, Қол, Аяқ',
                'image_filename': 'bodybuilding-program.jpg',
                'exercises': json.dumps({
                    'Күн 1 - Кеуде және Трицепс': [
                        {'name': 'Жатып сығымдау', 'sets': '4', 'reps': '8-12', 'rest': '90 сек'},
                        {'name': 'Еңіс орындықта гантель сығымдау', 'sets': '4', 'reps': '10-12', 'rest': '60 сек'},
                        {'name': 'Блокта ұшу', 'sets': '3', 'reps': '12-15', 'rest': '60 сек'},
                        {'name': 'Трицепс төмен итеру', 'sets': '4', 'reps': '12-15', 'rest': '60 сек'}
                    ],
                    'Күн 2 - Арқа және Бицепс': [
                        {'name': 'Өлі тарту', 'sets': '4', 'reps': '6-8', 'rest': '120 сек'},
                        {'name': 'Тартылу', 'sets': '4', 'reps': '8-12', 'rest': '90 сек'},
                        {'name': 'Штанга тартуы', 'sets': '3', 'reps': '10-12', 'rest': '60 сек'},
                        {'name': 'Бицепс бүгу', 'sets': '4', 'reps': '12-15', 'rest': '60 сек'}
                    ]
                })
            },
            {
                'title': '3x5 Толық дене күш бағдарламасы',
                'description': 'Негізгі қозғалыстарға бағытталған классикалық күш бағдарламасы.',
                'program_type': 'Күш',
                'fitness_level': 'Бастауыш',
                'duration': 12,
                'workout_frequency': 'Аптасына 3 күн',
                'equipment_needed': 'Штанга, Күш рамасы',
                'calories_burn': 400,
                'is_public': True,
                'target_muscle_groups': 'Толық дене, Кор',
                'image_filename': 'strength-program.jpg',
                'exercises': json.dumps({
                    'Жаттығу A': [
                        {'name': 'Отырып-тұру', 'sets': '5', 'reps': '5', 'rest': '180 сек'},
                        {'name': 'Жатып сығымдау', 'sets': '5', 'reps': '5', 'rest': '180 сек'},
                        {'name': 'Штанга тартуы', 'sets': '5', 'reps': '5', 'rest': '180 сек'}
                    ],
                    'Жаттығу B': [
                        {'name': 'Өлі тарту', 'sets': '5', 'reps': '5', 'rest': '180 сек'},
                        {'name': 'Иықтан көтеру', 'sets': '5', 'reps': '5', 'rest': '180 сек'},
                        {'name': 'Тартылу', 'sets': '3', 'reps': 'Максимум', 'rest': '180 сек'}
                    ]
                })
            },
            {
                'title': 'Әйелдерге арналған дене сымбатын жақсарту',
                'description': 'Әйелдерге арналған тонус пен пішінді жақсартуға бағытталған толық бағдарлама.',
                'program_type': 'Тонус',
                'fitness_level': 'Бастауыш',
                'duration': 6,
                'workout_frequency': 'Аптасына 4 күн',
                'equipment_needed': 'Гантельдер, Резеңке жолақтар',
                'calories_burn': 300,
                'is_public': True,
                'target_muscle_groups': 'Толық дене, Кор, Бөксе',
                'image_filename': 'womens-toning.jpg',
                'exercises': json.dumps({
                    'Күн 1 - Төменгі дене': [
                        {'name': 'Отырып-тұру', 'sets': '3', 'reps': '15', 'rest': '45 сек'},
                        {'name': 'Аяқ алға шығару', 'sets': '3', 'reps': 'әр жаққа 12', 'rest': '45 сек'},
                        {'name': 'Бөксе көпірі', 'sets': '3', 'reps': '20', 'rest': '45 сек'}
                    ],
                    'Күн 2 - Жоғарғы дене': [
                        {'name': 'Сүйеніп жатып көтерілу', 'sets': '3', 'reps': '10', 'rest': '45 сек'},
                        {'name': 'Резеңкемен тарту', 'sets': '3', 'reps': '15', 'rest': '45 сек'},
                        {'name': 'Жанға көтеру', 'sets': '3', 'reps': '12', 'rest': '45 сек'}
                    ]
                })
            },
            {
                'title': '5x5 Жоғары деңгейлі күш бағдарламасы',
                'description': 'Тәжірибелі спортшыларға арналған жоғары қарқынды күш бағдарламасы.',
                'program_type': 'Күш',
                'fitness_level': 'Жоғары',
                'duration': 12,
                'workout_frequency': 'Аптасына 4 күн',
                'equipment_needed': 'Толық жабдықталған спортзал',
                'calories_burn': 600,
                'is_public': True,
                'target_muscle_groups': 'Толық дене, Күш',
                'image_filename': 'advanced-strength.jpg',
                'exercises': json.dumps({
                    'Күн 1 - Күш': [
                        {'name': 'Күштік тартпа', 'sets': '5', 'reps': '3', 'rest': '180 сек'},
                        {'name': 'Алдыңғы отырып-тұру', 'sets': '5', 'reps': '5', 'rest': '180 сек'},
                        {'name': 'Әскери сығымдау', 'sets': '5', 'reps': '5', 'rest': '180 сек'}
                    ]
                })
            },
            {
                'title': 'HIIT кардио бағдарламасы',
                'description': 'Май жағу үшін жоғары қарқынды интервалды жаттығулар.',
                'program_type': 'Кардио',
                'fitness_level': 'Орташа',
                'duration': 4,
                'workout_frequency': 'Аптасына 3 күн',
                'equipment_needed': 'Минималды жабдық',
                'calories_burn': 400,
                'is_public': True,
                'target_muscle_groups': 'Толық дене, Кардио',
                'image_filename': 'hiit-cardio.jpg',
                'exercises': json.dumps({
                    'Шеңбер 1': [
                        {'name': 'Бурпи', 'sets': '3', 'reps': '30 сек', 'rest': '15 сек'},
                        {'name': 'Таудағы альпинист', 'sets': '3', 'reps': '30 сек', 'rest': '15 сек'},
                        {'name': 'Секіртпе', 'sets': '3', 'reps': '1 мин', 'rest': '30 сек'}
                    ]
                })
            },
            {
                'title': 'Итеру-Тарту-Аяқ бөлінісі',
                'description': 'Бұлшықет өсуіне арналған классикалық бодибилдинг бөлінісі.',
                'program_type': 'Бодибилдинг',
                'fitness_level': 'Орташа',
                'duration': 12,
                'workout_frequency': 'Аптасына 6 күн',
                'equipment_needed': 'Толық жабдықталған спортзал',
                'calories_burn': 500,
                'is_public': True,
                'target_muscle_groups': 'Толық дене бөлінісі',
                'image_filename': 'push-pull-legs.jpg',
                'exercises': json.dumps({
                    'Итеру күні': [
                        {'name': 'Жатып сығымдау', 'sets': '4', 'reps': '8-12', 'rest': '90 сек'},
                        {'name': 'Иықтан көтеру', 'sets': '4', 'reps': '8-12', 'rest': '90 сек'},
                        {'name': 'Трицепс созу', 'sets': '3', 'reps': '12-15', 'rest': '60 сек'}
                    ],
                    'Тарту күні': [
                        {'name': 'Тартылу', 'sets': '4', 'reps': '8-12', 'rest': '90 сек'},
                        {'name': 'Штанга тартуы', 'sets': '4', 'reps': '8-12', 'rest': '90 сек'},
                        {'name': 'Бицепс бүгу', 'sets': '3', 'reps': '12-15', 'rest': '60 сек'}
                    ],
                    'Аяқ күні': [
                        {'name': 'Отырып-тұру', 'sets': '4', 'reps': '8-12', 'rest': '120 сек'},
                        {'name': 'Румын өлі тартуы', 'sets': '4', 'reps': '8-12', 'rest': '90 сек'},
                        {'name': 'Балтыр көтеру', 'sets': '3', 'reps': '15-20', 'rest': '60 сек'}
                    ]
                })
            }
        ]

        for program_data in programs:
            program = WorkoutProgram(
                user_id=system_user.id,
                **program_data
            )
            db.session.add(program)

        db.session.commit()

def add_sample_exercises():
    with app.app_context():
        # Check if we already have sample exercises
        if Exercise.query.filter_by(name='Bench Press').first():
            return

        # Create a system user if not exists
        system_user = User.query.filter_by(username='system').first()
        if not system_user:
            system_user = User(
                username='system',
                email='system@fitness.local',
                password_hash=generate_password_hash('system_password')
            )
            db.session.add(system_user)
            db.session.commit()

        # Sample exercises by muscle group
        exercises = [
            {
                'name': 'Bench Press',
                'name_kz': 'Жатып итеру',
                'description': 'Classic compound exercise for chest development',
                'description_kz': 'Кеуде бұлшықетін дамытуға арналған классикалық құрама жаттығу',
                'muscle_group': 'Chest',
                'secondary_muscles': 'Triceps, Shoulders',
                'equipment': 'Barbell, Bench',
                'difficulty': 'Intermediate',
                'instructions_kz': '1. Орындықта арқаңызбен жатыңыз\n2. Штанганы иық еніне сәйкес ұстаңыз\n3. Кеудеңізге дейін түсіріңіз\n4. Қолыңызды толық жазғанша итеріңіз'
            },
            {
                'name': 'Dumbbell Flies',
                'name_kz': 'Гантельмен ұшу',
                'description': 'Isolation exercise for chest',
                'description_kz': 'Кеуде бұлшықетіне арналған оқшаулау жаттығуы',
                'muscle_group': 'Chest',
                'secondary_muscles': 'Shoulders',
                'equipment': 'Dumbbells, Bench',
                'difficulty': 'Beginner',
                'instructions_kz': '1. Орындықта арқаңызбен жатыңыз\n2. Гантельдерді кеуде деңгейінде ұстаңыз\n3. Қолдарыңызды жанға қарай созыңыз\n4. Бастапқы қалыпқа қайтыңыз'
            },
            {
                'name': 'Pull-ups',
                'name_kz': 'Тартылу',
                'description': 'Compound exercise for back width',
                'description_kz': 'Арқа енін дамытуға арналған құрама жаттығу',
                'muscle_group': 'Back',
                'secondary_muscles': 'Biceps, Shoulders',
                'equipment': 'Pull-up Bar',
                'difficulty': 'Advanced',
                'instructions_kz': '1. Турникті жоғарыдан ұстаңыз\n2. Иегіңіз турник деңгейіне жеткенше тартылыңыз\n3. Баяу түсіңіз\n4. Қолдарыңызды толық созыңыз'
            },
            {
                'name': 'Barbell Rows',
                'name_kz': 'Штанганы тарту',
                'description': 'Compound exercise for back thickness',
                'description_kz': 'Арқа қалыңдығын дамытуға арналған құрама жаттығу',
                'muscle_group': 'Back',
                'secondary_muscles': 'Biceps, Rear Delts',
                'equipment': 'Barbell',
                'difficulty': 'Intermediate',
                'instructions_kz': '1. Штанганы иық еніне сәйкес ұстаңыз\n2. Беліңізді сәл бүгіңіз\n3. Штанганы кеудеңізге дейін тартыңыз\n4. Баяу түсіріңіз'
            },
            {
                'name': 'Military Press',
                'name_kz': 'Әскери итеру',
                'description': 'Compound exercise for shoulder development',
                'description_kz': 'Иық бұлшықетін дамытуға арналған құрама жаттығу',
                'muscle_group': 'Shoulders',
                'secondary_muscles': 'Triceps',
                'equipment': 'Barbell',
                'difficulty': 'Intermediate',
                'instructions_kz': '1. Штанганы иықта ұстаңыз\n2. Тік тұрыңыз\n3. Штанганы басыңыздың үстіне көтеріңіз\n4. Баяу түсіріңіз'
            },
            {
                'name': 'Squats',
                'name_kz': 'Отырып-тұру',
                'description': 'King of leg exercises',
                'description_kz': 'Аяқ жаттығуларының королі',
                'muscle_group': 'Legs',
                'secondary_muscles': 'Core, Lower Back',
                'equipment': 'Barbell',
                'difficulty': 'Intermediate',
                'instructions_kz': '1. Штанганы иықта ұстаңыз\n2. Аяқтарыңызды иық еніне қойыңыз\n3. Тізеңізді 90 градусқа бүгіңіз\n4. Бастапқы қалыпқа оралыңыз'
            },
            {
                'name': 'Bicep Curls',
                'name_kz': 'Бицепс бүгу',
                'description': 'Classic bicep builder',
                'description_kz': 'Классикалық бицепс қалыптастырушы',
                'muscle_group': 'Biceps',
                'secondary_muscles': 'Forearms',
                'equipment': 'Dumbbells',
                'difficulty': 'Beginner',
                'instructions_kz': '1. Гантельдерді төмен түсіріп тұрыңыз\n2. Қолыңызды бүгіңіз\n3. Иыққа дейін көтеріңіз\n4. Баяу түсіріңіз'
            },
            {
                'name': 'Tricep Pushdowns',
                'name_kz': 'Трицепс итеру',
                'description': 'Isolation exercise for triceps',
                'description_kz': 'Трицепске арналған оқшаулау жаттығуы',
                'muscle_group': 'Triceps',
                'equipment': 'Cable Machine',
                'difficulty': 'Beginner',
                'instructions_kz': '1. Тұтқаны жоғарыдан ұстаңыз\n2. Шынтақты бүкпей қолды төмен итеріңіз\n3. Толық қозғалыс жасаңыз\n4. Баяу қайтарыңыз'
            }
        ]

        for exercise_data in exercises:
            exercise = Exercise.query.filter_by(name=exercise_data['name']).first()
            if not exercise:
                exercise = Exercise(**exercise_data)
                db.session.add(exercise)
        
        db.session.commit()

@app.route('/exercises')
def exercises():
    # Get filter parameters
    muscle_group = request.args.get('muscle_group', 'All')
    difficulty = request.args.get('difficulty', 'All')
    equipment = request.args.get('equipment', 'All')

    # Base query
    query = Exercise.query

    # Apply filters
    if muscle_group != 'All':
        query = query.filter_by(muscle_group=muscle_group)
    if difficulty != 'All':
        query = query.filter_by(difficulty=difficulty)
    if equipment != 'All':
        query = query.filter(Exercise.equipment.contains(equipment))

    # Get exercises
    exercises = query.all()

    # Translate categories for display
    for exercise in exercises:
        exercise.muscle_group = MUSCLE_GROUP_TRANSLATIONS.get(exercise.muscle_group, exercise.muscle_group)
        exercise.difficulty = DIFFICULTY_TRANSLATIONS.get(exercise.difficulty, exercise.difficulty)
        if exercise.equipment:
            equipment_list = exercise.equipment.split(',')
            translated_equipment = [EQUIPMENT_TRANSLATIONS.get(eq.strip(), eq.strip()) for eq in equipment_list]
            exercise.equipment = ', '.join(translated_equipment)
        
        if exercise.secondary_muscles:
            muscles_list = exercise.secondary_muscles.split(',')
            translated_muscles = [MUSCLE_GROUP_TRANSLATIONS.get(m.strip(), m.strip()) for m in muscles_list]
            exercise.secondary_muscles = ', '.join(translated_muscles)

    return render_template('exercises.html',
                         exercises=exercises,
                         muscle_groups=list(MUSCLE_GROUP_TRANSLATIONS.values()),
                         difficulties=list(DIFFICULTY_TRANSLATIONS.values()),
                         equipment_list=list(EQUIPMENT_TRANSLATIONS.values()))

def request_wants_json():
    """Check if the request prefers JSON response."""
    if not has_request_context():
        return False
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return (best == 'application/json' and
            request.accept_mimetypes[best] > request.accept_mimetypes['text/html'])

def is_xhr():
    """Check if the request was made via AJAX."""
    if not has_request_context():
        return False
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request_wants_json()

if __name__ == '__main__':
    with app.app_context():
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        db.create_all()
        add_sample_programs()
        add_sample_exercises()
    app.run(debug=True) 
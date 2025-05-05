from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, IntegerField, BooleanField, FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange
from flask_wtf.file import FileAllowed

class LoginForm(FlaskForm):
    username = StringField('Пайдаланушы аты', 
                         validators=[DataRequired(message='Пайдаланушы атын енгізіңіз')])
    password = PasswordField('Құпия сөз', 
                           validators=[DataRequired(message='Құпия сөзді енгізіңіз')])
    remember = BooleanField('Мені есте сақтау')

class RegistrationForm(FlaskForm):
    username = StringField('Пайдаланушы аты', 
                         validators=[DataRequired(message='Пайдаланушы атын енгізіңіз'),
                                   Length(min=3, max=20, message='Пайдаланушы аты 3-20 таңба аралығында болуы керек')])
    email = StringField('Электрондық пошта',
                       validators=[DataRequired(message='Email енгізіңіз'),
                                 Email(message='Жарамды email енгізіңіз')])
    password = PasswordField('Құпия сөз',
                           validators=[DataRequired(message='Құпия сөзді енгізіңіз'),
                                     Length(min=6, message='Құпия сөз кемінде 6 таңбадан тұруы керек')])
    confirm_password = PasswordField('Құпия сөзді қайталаңыз',
                                   validators=[DataRequired(message='Құпия сөзді қайта енгізіңіз'),
                                             EqualTo('password', message='Құпия сөздер сәйкес келмейді')])

class ProgramForm(FlaskForm):
    name = StringField('Бағдарлама атауы',
                      validators=[DataRequired(message='Бағдарлама атауын енгізіңіз')])
    description = TextAreaField('Сипаттама',
                              validators=[DataRequired(message='Сипаттаманы енгізіңіз')])
    category = SelectField('Санат',
                         choices=[
                             ('strength', 'Күш жаттығулары'),
                             ('cardio', 'Кардио'),
                             ('flexibility', 'Икемділік'),
                             ('hiit', 'HIIT'),
                             ('general', 'Жалпы')
                         ])
    difficulty = SelectField('Қиындық деңгейі',
                           choices=[
                               ('beginner', 'Бастаушы'),
                               ('intermediate', 'Орташа'),
                               ('advanced', 'Жоғары')
                           ])
    duration = IntegerField('Ұзақтығы (минут)',
                          validators=[DataRequired(message='Ұзақтығын енгізіңіз'),
                                    NumberRange(min=1, message='Ұзақтығы 1 минуттан көп болуы керек')])
    image = FileField('Бағдарлама суреті',
                     validators=[FileAllowed(['jpg', 'png'], 'Тек JPG және PNG файлдарына рұқсат етіледі')])

class GoalForm(FlaskForm):
    title = StringField('Мақсат атауы',
                       validators=[DataRequired(message='Мақсат атауын енгізіңіз')])
    description = TextAreaField('Сипаттама',
                              validators=[DataRequired(message='Сипаттаманы енгізіңіз')])
    target_date = StringField('Мерзімі',
                            validators=[DataRequired(message='Мерзімін енгізіңіз')])
    target_value = IntegerField('Мақсатты мән',
                              validators=[DataRequired(message='Мақсатты мәнді енгізіңіз'),
                                        NumberRange(min=1, message='Мақсатты мән 1-ден көп болуы керек')])
    unit = SelectField('Өлшем бірлігі',
                      choices=[
                          ('kg', 'Килограмм'),
                          ('reps', 'Қайталау'),
                          ('sets', 'Сет'),
                          ('minutes', 'Минут'),
                          ('days', 'Күн')
                      ])

class WorkoutLogForm(FlaskForm):
    duration = IntegerField('Ұзақтығы (минут)',
                          validators=[DataRequired(message='Ұзақтығын енгізіңіз')])
    intensity = SelectField('Қарқындылық',
                          choices=[
                              ('low', 'Төмен'),
                              ('medium', 'Орташа'),
                              ('high', 'Жоғары')
                          ])
    notes = TextAreaField('Қосымша жазбалар') 
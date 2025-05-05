from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app import app, db, Exercise

migrate = Migrate(app, db)

def upgrade():
    # Add Kazakh translation columns
    with app.app_context():
        db.engine.execute('''
            ALTER TABLE exercise 
            ADD COLUMN name_kz VARCHAR(100),
            ADD COLUMN description_kz TEXT,
            ADD COLUMN instructions_kz TEXT
        ''')
        
        # Update existing exercises with translations
        translations = {
            'Bench Press': {
                'name_kz': 'Жатып итеру',
                'description_kz': 'Кеуде бұлшықетін дамытуға арналған классикалық құрама жаттығу',
                'instructions_kz': '1. Орындықта арқаңызбен жатыңыз\n2. Штанганы иық еніне сәйкес ұстаңыз\n3. Кеудеңізге дейін түсіріңіз\n4. Қолыңызды толық жазғанша итеріңіз'
            },
            'Dumbbell Flies': {
                'name_kz': 'Гантельмен ұшу',
                'description_kz': 'Кеуде бұлшықетіне арналған оқшаулау жаттығуы',
                'instructions_kz': '1. Орындықта арқаңызбен жатыңыз\n2. Гантельдерді кеуде деңгейінде ұстаңыз\n3. Қолдарыңызды жанға қарай созыңыз\n4. Бастапқы қалыпқа қайтыңыз'
            },
            'Pull-ups': {
                'name_kz': 'Тартылу',
                'description_kz': 'Арқа енін дамытуға арналған құрама жаттығу',
                'instructions_kz': '1. Турникті жоғарыдан ұстаңыз\n2. Иегіңіз турник деңгейіне жеткенше тартылыңыз\n3. Баяу түсіңіз\n4. Қолдарыңызды толық созыңыз'
            },
            'Barbell Rows': {
                'name_kz': 'Штанганы тарту',
                'description_kz': 'Арқа қалыңдығын дамытуға арналған құрама жаттығу',
                'instructions_kz': '1. Штанганы иық еніне сәйкес ұстаңыз\n2. Беліңізді сәл бүгіңіз\n3. Штанганы кеудеңізге дейін тартыңыз\n4. Баяу түсіріңіз'
            },
            'Military Press': {
                'name_kz': 'Әскери итеру',
                'description_kz': 'Иық бұлшықетін дамытуға арналған құрама жаттығу',
                'instructions_kz': '1. Штанганы иықта ұстаңыз\n2. Тік тұрыңыз\n3. Штанганы басыңыздың үстіне көтеріңіз\n4. Баяу түсіріңіз'
            },
            'Squats': {
                'name_kz': 'Отырып-тұру',
                'description_kz': 'Аяқ жаттығуларының королі',
                'instructions_kz': '1. Штанганы иықта ұстаңыз\n2. Аяқтарыңызды иық еніне қойыңыз\n3. Тізеңізді 90 градусқа бүгіңіз\n4. Бастапқы қалыпқа оралыңыз'
            },
            'Bicep Curls': {
                'name_kz': 'Бицепс бүгу',
                'description_kz': 'Классикалық бицепс қалыптастырушы',
                'instructions_kz': '1. Гантельдерді төмен түсіріп тұрыңыз\n2. Қолыңызды бүгіңіз\n3. Иыққа дейін көтеріңіз\n4. Баяу түсіріңіз'
            },
            'Tricep Pushdowns': {
                'name_kz': 'Трицепс итеру',
                'description_kz': 'Трицепске арналған оқшаулау жаттығуы',
                'instructions_kz': '1. Тұтқаны жоғарыдан ұстаңыз\n2. Шынтақты бүкпей қолды төмен итеріңіз\n3. Толық қозғалыс жасаңыз\n4. Баяу қайтарыңыз'
            }
        }
        
        for exercise in Exercise.query.all():
            if exercise.name in translations:
                trans = translations[exercise.name]
                exercise.name_kz = trans['name_kz']
                exercise.description_kz = trans['description_kz']
                exercise.instructions_kz = trans['instructions_kz']
        
        db.session.commit()

def downgrade():
    # Remove Kazakh translation columns
    with app.app_context():
        db.engine.execute('''
            ALTER TABLE exercise 
            DROP COLUMN name_kz,
            DROP COLUMN description_kz,
            DROP COLUMN instructions_kz
        ''')

if __name__ == '__main__':
    upgrade() 
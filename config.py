import os
import secrets

class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///fitness.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File uploads
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm'}
    
    # Messages
    MESSAGES = {
        'kk': {
            'login_success': 'Сәтті кірдіңіз!',
            'logout_success': 'Сәтті шықтыңыз!',
            'register_success': 'Тіркелу сәтті аяқталды!',
            'username_exists': 'Бұл пайдаланушы аты бос емес',
            'email_exists': 'Бұл email бос емес',
            'passwords_dont_match': 'Құпия сөздер сәйкес келмейді',
            'invalid_credentials': 'Қате пайдаланушы аты немесе құпия сөз',
            'file_not_allowed': 'Бұл файл түріне рұқсат етілмеген',
            'program_created': 'Бағдарлама сәтті құрылды!',
            'program_updated': 'Бағдарлама сәтті жаңартылды!',
            'program_deleted': 'Бағдарлама сәтті жойылды!',
            'goal_created': 'Мақсат сәтті құрылды!',
            'goal_updated': 'Мақсат сәтті жаңартылды!',
            'goal_deleted': 'Мақсат сәтті жойылды!',
            'reminder_created': 'Еске салғыш сәтті құрылды!',
            'reminder_updated': 'Еске салғыш сәтті жаңартылды!',
            'reminder_deleted': 'Еске салғыш сәтті жойылды!',
            'no_permission': 'Бұл әрекетке рұқсатыңыз жоқ',
            'image_upload_success': 'Сурет сәтті жүктелді!',
            'image_upload_error': 'Сурет жүктеу кезінде қате орын алды',
            'file_too_large': 'Файл тым үлкен (максимум 16MB)',
        }
    }
    
    # Categories
    MUSCLE_GROUP_TRANSLATIONS = {
        'Chest': 'Кеуде',
        'Back': 'Арқа',
        'Shoulders': 'Иық',
        'Legs': 'Аяқ',
        'Biceps': 'Бицепс',
        'Triceps': 'Трицепс',
        'Core': 'Кор',
        'Full Body': 'Толық дене',
        'Cardio': 'Кардио'
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
        'Dumbbells': 'Гантельдер',
        'Resistance Bands': 'Резеңке жолақтар',
        'Kettlebell': 'Гиря',
        'None': 'Жабдықсыз'
    }
    
    PROGRAM_TYPE_TRANSLATIONS = {
        'Strength': 'Күш',
        'Hypertrophy': 'Бұлшықет өсуі',
        'Endurance': 'Төзімділік',
        'Weight Loss': 'Салмақ тастау',
        'Cardio': 'Кардио',
        'Flexibility': 'Икемділік'
    } 
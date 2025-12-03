from bisect import bisect_left
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
import random

db = SQLAlchemy()

# ==================== Database Models ====================

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    api_token = db.Column(db.String(255), unique=True, nullable=False)
    profile_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    health_records = db.relationship('HealthRecord', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    hr_records = db.relationship('HRRecord', backref='user', lazy='dynamic', cascade='all, delete-orphan')


class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sex = db.Column(db.String(10), nullable=False)  # 'M' or 'F'
    age = db.Column(db.Integer, nullable=False)
    chest_pain_type = db.Column(db.String(50), nullable=False)
    exercise_angina = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class HealthRecord(db.Model):
    __tablename__ = 'health_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    resting_bp = db.Column(db.Integer, nullable=False)
    cholesterol = db.Column(db.Integer, nullable=False)
    fasting_bs = db.Column(db.Boolean, nullable=False)  # True if > 120 mg/dl
    timestamp = db.Column(db.DateTime, default=datetime.now)


class HRRecord(db.Model):
    __tablename__ = 'hr_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    heart_rate = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)


# ==================== Database Initialization ====================

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()


# ==================== User Functions ====================

def create_user(google_id: str, email: str, name: str, api_token: str) -> User:
    user = User(
        google_id=google_id,
        email=email,
        name=name,
        api_token=api_token,
        profile_completed=False
    )
    db.session.add(user)
    db.session.commit()
    return user


def get_user_by_google_id(google_id: str) -> User:
    return User.query.filter_by(google_id=google_id).first()

def get_user_by_token(api_token: str) -> User:
    return User.query.filter_by(api_token=api_token).first()


# ==================== Profile Functions ====================

def update_userdata(user_id: int, data: dict) -> dict:
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}
    
    if user.profile:
        # Update existing profile
        user.profile.sex = data["sex"]
        user.profile.age = data["age"]
        user.profile.chest_pain_type = data["chest_pain_type"]
        user.profile.exercise_angina = data["exercise_angina"]
    else:
        # Create new profile
        profile = UserProfile(
            user_id=user_id,
            sex=data["sex"],
            age=data["age"],
            chest_pain_type=data["chest_pain_type"],
            exercise_angina=data["exercise_angina"]
        )
        db.session.add(profile)
    
    user.profile_completed = True
    db.session.commit()
    
    return {"message": "Profile updated successfully"}


# ==================== Health Record Functions ====================

def add_health_record(user_id: int, data: dict) -> dict:
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}
    
    # Delete too old records OR records from today (keep only latest per day)
    cutoff_time = datetime.now() - timedelta(days=30)
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    HealthRecord.query.filter(
        HealthRecord.user_id == user_id,
        or_(
            HealthRecord.timestamp < cutoff_time,
            HealthRecord.timestamp >= today_start  # Delete today's old records
        )
    ).delete()


    
    # Convert fasting_bs to boolean (True if > 120 mg/dl)
    fasting_bs_value = data["fasting_bs"]
    if isinstance(fasting_bs_value, bool):
        fasting_bs_bool = fasting_bs_value
    else:
        fasting_bs_bool = int(fasting_bs_value) > 120
    
    record = HealthRecord(
        user_id=user_id,
        resting_bp=data["resting_bp"],
        cholesterol=data["cholesterol"],
        fasting_bs=fasting_bs_bool
    )
    db.session.add(record)
    db.session.commit()
    
    return {"message": "Health record added successfully"}


def get_health_data(user_id: int) -> dict:
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}
    
    records = user.health_records.order_by(HealthRecord.timestamp.desc()).all()
    health_data = [{
        "resting_bp": r.resting_bp,
        "cholesterol": r.cholesterol,
        "fasting_bs": r.fasting_bs,
        "timestamp": r.timestamp.isoformat()
    } for r in records]
    return {"health_data": health_data}


# ==================== Chart Data Functions ====================

def add_hr_record(user_id: int, heart_rate: int) -> dict:
    # Delete too old records
    cutoff_time = datetime.now() - timedelta(days=7)
    HRRecord.query.filter(
        HRRecord.user_id == user_id,
        HRRecord.timestamp < cutoff_time
    ).delete()

    record = HRRecord(
        user_id=user_id,
        heart_rate=heart_rate
    )
    db.session.add(record)
    db.session.commit()
    return {"message": "HR record added successfully"}


def get_chart_data(user_id: int, points: int, data_type: str = 'hr') -> dict:
    user = User.query.get(user_id)
    
    if data_type == 'hr':
        records = HRRecord.query.filter_by(user_id=user_id)\
            .order_by(HRRecord.timestamp.desc())\
            .limit(points).all()
        
        if records:
            records.reverse()
            labels = [r.timestamp.strftime('%H:%M') for r in records]
            values = [r.heart_rate for r in records]
            if points >= 43200:
                labels = [(datetime.now() - timedelta(minutes=i)).strftime('%Y-%m-%d %H:%M') for i in range(points)][::-1]
                new_values = []
                j = 0
                for i in values:
                    temp = 0
                    if i:
                        temp += i
                    j += 1
                    if j == 30:
                        new_values.append(temp // 30 if temp != 0 else None)
                        j = 0
                values = new_values
        else:
            return {"labels": [], "values": []}
    else:  # bp
        records = HealthRecord.query.filter_by(user_id=user_id)\
            .order_by(HealthRecord.timestamp.desc())\
            .limit(points).all()
        
        if records:
            records.reverse()
            labels = [r.timestamp.strftime('%Y-%m-%d') for r in records]
            values = [r.resting_bp for r in records]
            for t in [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(points)][::-1]:
                if t not in labels:
                    idx = bisect_left(labels, t)
                    labels.insert(idx, t)
                    values.insert(idx, None)
        else:
            return {"labels": [], "values": []}
    return {"labels": labels, "values": values}


# ==================== Health Summary Functions ====================

def get_health_summary(user_id: int) -> dict:
    user = User.query.get(user_id)
    
    # Get latest health record
    latest_health = HealthRecord.query.filter_by(user_id=user_id)\
        .order_by(HealthRecord.timestamp.desc()).first()
    
    # Get latest HR records for avg/max calculation
    hr_records = HRRecord.query.filter_by(user_id=user_id)\
        .order_by(HRRecord.timestamp.desc()).limit(100).all()
    
    if hr_records:
        avg_hr = sum(r.heart_rate for r in hr_records) // len(hr_records)
        max_hr = max(r.heart_rate for r in hr_records)
    else:
        avg_hr = random.randint(70, 80)
        max_hr = random.randint(150, 160)
    
    resting_bp = latest_health.resting_bp if latest_health else random.randint(115, 125)
    
    return {
        "last_update": datetime.now().isoformat(),
        "overview": {
            "resting_bp": resting_bp,
            "avg_hr": avg_hr,
            "max_hr": max_hr,
            "oldpeak": round(random.uniform(0.5, 1.2), 1)  # TODO: Calculate from ECG data
        },
        "ai_summary": "這是來自 Python 後端的 AI 健康建議。請保持規律運動並監測您的心率。"
    }
import argparse
import os
import random

from bisect import bisect_left
from datetime import datetime, timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_

import result_data

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
            earliest_time = (datetime.now() - timedelta(minutes=points)).timestamp()
            while records and records[-1].timestamp.timestamp() < earliest_time:
                records.pop()
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
            earliest_time = (datetime.now() - timedelta(days=points)).timestamp()
            while records and records[-1].timestamp.timestamp() < earliest_time:
                records.pop()
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
        # max_hr = max(r.heart_rate for r in hr_records)
    else:
        avg_hr = random.randint(70, 80)
        # max_hr = random.randint(150, 160)
    
    resting_bp = latest_health.resting_bp if latest_health else random.randint(115, 125)

    user_info = {}
    user_info["Age"] = UserProfile.query.filter_by(user_id=user_id).first().age if UserProfile.query.filter_by(user_id=user_id).first() else 0
    user_info["Sex"] = UserProfile.query.filter_by(user_id=user_id).first().sex if UserProfile.query.filter_by(user_id=user_id).first() else "M"
    user_info["ChestPainType"] = UserProfile.query.filter_by(user_id=user_id).first().chest_pain_type if UserProfile.query.filter_by(user_id=user_id).first() else "ASY"
    user_info["ExerciseAngina"] = UserProfile.query.filter_by(user_id=user_id).first().exercise_angina if UserProfile.query.filter_by(user_id=user_id).first() else 0
    user_info["ExerciseAngina"] = "Y" if user_info["ExerciseAngina"] != 0 else "N"
    user_info["RestingBP"] = resting_bp
    user_info["Cholesterol"] = latest_health.cholesterol if latest_health else random.randint(150, 200)
    user_info["FastingBS"] = latest_health.fasting_bs if latest_health else 0
    user_other_info = result_data.parse_user_info(user_info)
    
    return {
        "last_update": datetime.now().isoformat(),
        "overview": {
            "resting_bp": resting_bp,
            "avg_hr": avg_hr,
            "max_hr": user_other_info["max_hr"],
            "oldpeak": user_other_info["oldpeak"],
            "st_slope": user_other_info["st_slope"]
        },
        "ai_summary": "這是來自 Python 後端的 AI 健康建議。請保持規律運動並監測您的心率。"
    }

# ==================== Database Debug Tools ====================

def clear_database():
    db.session.query(UserProfile).delete()
    db.session.query(HealthRecord).delete()
    db.session.query(HRRecord).delete()
    db.session.query(User).delete()
    db.session.commit()

def show_all_tables():
    print("\n" + "="*80)
    print("DATABASE CONTENT")
    print("="*80)
    
    # Users table
    users = User.query.all()
    print(f"\n📋 USERS ({len(users)} records)")
    print("-" * 80)
    if users:
        print(f"{'ID':<5} {'Google ID':<15} {'Name':<20} {'Email':<30} {'Completed':<10}")
        print("-" * 80)
        for user in users:
            print(f"{user.id:<5} {user.google_id[:14]:<15} {user.name[:19]:<20} {user.email[:29]:<30} {user.profile_completed:<10}")
    else:
        print("(No users found)")
    
    # User Profiles table
    profiles = UserProfile.query.all()
    print(f"\n👤 USER PROFILES ({len(profiles)} records)")
    print("-" * 60)
    if profiles:
        print(f"{'ID':<5} {'User ID':<8} {'Sex':<5} {'Age':<5} {'Chest Pain':<15} {'Ex.Angina':<10}")
        print("-" * 60)
        for profile in profiles:
            print(f"{profile.id:<5} {profile.user_id:<8} {profile.sex:<5} {profile.age:<5} {profile.chest_pain_type[:14]:<15} {profile.exercise_angina:<10}")
    else:
        print("(No profiles found)")
    
    # Health Records table
    health_records = HealthRecord.query.all()
    print(f"\n🏥 HEALTH RECORDS ({len(health_records)} records)")
    print("-" * 70)
    if health_records:
        print(f"{'ID':<5} {'User ID':<8} {'BP':<5} {'Chol':<5} {'FastBS':<8} {'Timestamp':<19}")
        print("-" * 70)
        for record in health_records:
            print(f"{record.id:<5} {record.user_id:<8} {record.resting_bp:<5} {record.cholesterol:<5} {record.fasting_bs:<8} {record.timestamp.strftime('%Y-%m-%d %H:%M:%S'):<19}")
    else:
        print("(No health records found)")
    
    # HR Records table  
    hr_records = HRRecord.query.order_by(HRRecord.timestamp.desc()).limit(10).all()
    total_hr = HRRecord.query.count()
    print(f"\n❤️  HR RECORDS ({total_hr} total, showing last 10)")
    print("-" * 50)
    if hr_records:
        print(f"{'ID':<5} {'User ID':<8} {'HR':<5} {'Timestamp':<19}")
        print("-" * 50)
        for record in hr_records:
            print(f"{record.id:<5} {record.user_id:<8} {record.heart_rate:<5} {record.timestamp.strftime('%Y-%m-%d %H:%M:%S'):<19}")
    else:
        print("(No HR records found)")
    
    print("\n" + "="*80)

def delete_user_by_id(user_id: int):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return {"message": f"User {user_id} and related data deleted successfully"}
    else:
        return {"error": "User not found"}

if __name__ == '__main__':
    # Create a minimal Flask app for database operations
    app = Flask(__name__)
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(data_dir, "data.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    parser = argparse.ArgumentParser(description='Database operations')
    parser.add_argument('command', choices=['show_all_tables', 'clear_database', 'delete_user'], 
                       help='Database command to execute')
    parser.add_argument('--user_id', type=int, help='User ID to delete (required for delete_user command)')
    
    args = parser.parse_args()
    
    init_db(app)
    
    with app.app_context():
        if args.command == 'show_all_tables':
            show_all_tables()
            print("All tables displayed successfully!")
        elif args.command == 'clear_database':
            clear_database()
            print("Database cleared successfully!")
        elif args.command == 'delete_user':
            if args.user_id is None:
                print("Error: --user_id is required for delete_user command")
            else:
                result = delete_user_by_id(args.user_id)
                print(result.get("message") or result.get("error"))
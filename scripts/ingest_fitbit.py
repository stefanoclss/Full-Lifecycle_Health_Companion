import os
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Date
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_DIR = os.path.join(DATA_DIR, "db")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads", "fitbit_data")
DB_PATH = os.path.join(DB_DIR, "health_companion.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Ensure DB directory exists
os.makedirs(DB_DIR, exist_ok=True)

# --- Database Setup ---
Base = declarative_base()

class DailyActivity(Base):
    __tablename__ = 'daily_activity'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    activity_date = Column(Date)
    total_steps = Column(Integer)
    total_distance = Column(Float)
    tracker_distance = Column(Float)
    logged_activities_distance = Column(Float)
    very_active_distance = Column(Float)
    moderately_active_distance = Column(Float)
    light_active_distance = Column(Float)
    sedentary_active_distance = Column(Float)
    very_active_minutes = Column(Integer)
    fairly_active_minutes = Column(Integer)
    lightly_active_minutes = Column(Integer)
    sedentary_minutes = Column(Integer)
    calories = Column(Integer)

class HourlySteps(Base):
    __tablename__ = 'hourly_steps'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    activity_hour = Column(DateTime)
    step_total = Column(Integer)

class MinuteSteps(Base):
    __tablename__ = 'minute_steps'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    activity_minute = Column(DateTime)
    steps = Column(Integer)

class SleepLog(Base):
    __tablename__ = 'sleep_log'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    sleep_day = Column(Date) # Note: sleepDay_merged.csv has time but it's usually 12:00:00 AM
    total_sleep_records = Column(Integer)
    total_minutes_asleep = Column(Integer)
    total_time_in_bed = Column(Integer)

class HeartRate(Base):
    __tablename__ = 'heart_rate'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    time = Column(DateTime)
    value = Column(Integer)

# --- Ingestion Logic ---

def get_primary_user_id(uploads_dir):
    """
    Scans all CSVs to find the most frequent User ID.
    """
    user_counts = {}
    
    for filename in os.listdir(uploads_dir):
        if not filename.endswith(".csv"):
            continue
            
        file_path = os.path.join(uploads_dir, filename)
        try:
            # Read only the 'Id' column to be fast
            df = pd.read_csv(file_path, usecols=['Id'])
            counts = df['Id'].value_counts().to_dict()
            
            for user_id, count in counts.items():
                user_id_str = str(user_id)
                user_counts[user_id_str] = user_counts.get(user_id_str, 0) + count
                
        except Exception as e:
            print(f"Skipping check of {filename} due to error: {e}")
            continue

    if not user_counts:
        return None

    # Return the user ID with the highest total row count across all files
    primary_user = max(user_counts, key=user_counts.get)
    print(f"Identified primary User ID: {primary_user} (found {user_counts[primary_user]} records)")
    return primary_user

def parse_date(date_str):
    """Parses various date formats found in Fitbit CSVs."""
    try:
        return pd.to_datetime(date_str, format="%m/%d/%Y")
    except:
        pass
    try:
        return pd.to_datetime(date_str, format="%m/%d/%Y %I:%M:%S %p")
    except:
        return pd.to_datetime(date_str) # Let pandas guess as fallback

def ingest_data():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    print(f"Scanning {UPLOADS_DIR}...")
    primary_user_id = get_primary_user_id(UPLOADS_DIR)
    
    if not primary_user_id:
        print("No CSV files or user IDs found.")
        return

    # 1. Daily Activity
    try:
        file_path = os.path.join(UPLOADS_DIR, "dailyActivity_merged.csv")
        if os.path.exists(file_path):
            print("Importing Daily Activity...")
            df = pd.read_csv(file_path)
            df['Id'] = df['Id'].astype(str)
            df = df[df['Id'] == primary_user_id]
            
            for _, row in df.iterrows():
                record = DailyActivity(
                    user_id=row['Id'],
                    activity_date=parse_date(row['ActivityDate']).date(),
                    total_steps=row['TotalSteps'],
                    total_distance=row['TotalDistance'],
                    tracker_distance=row['TrackerDistance'],
                    logged_activities_distance=row['LoggedActivitiesDistance'],
                    very_active_distance=row['VeryActiveDistance'],
                    moderately_active_distance=row['ModeratelyActiveDistance'],
                    light_active_distance=row['LightActiveDistance'],
                    sedentary_active_distance=row['SedentaryActiveDistance'],
                    very_active_minutes=row['VeryActiveMinutes'],
                    fairly_active_minutes=row['FairlyActiveMinutes'],
                    lightly_active_minutes=row['LightlyActiveMinutes'],
                    sedentary_minutes=row['SedentaryMinutes'],
                    calories=row['Calories']
                )
                session.add(record)
            session.commit()
    except Exception as e:
        print(f"Error importing Daily Activity: {e}")
        session.rollback()

    # 2. Hourly Steps
    try:
        file_path = os.path.join(UPLOADS_DIR, "hourlySteps_merged.csv")
        if os.path.exists(file_path):
            print("Importing Hourly Steps...")
            df = pd.read_csv(file_path)
            df['Id'] = df['Id'].astype(str)
            df = df[df['Id'] == primary_user_id]

            for _, row in df.iterrows():
                record = HourlySteps(
                    user_id=row['Id'],
                    activity_hour=parse_date(row['ActivityHour']),
                    step_total=row['StepTotal']
                )
                session.add(record)
            session.commit()
    except Exception as e:
        print(f"Error importing Hourly Steps: {e}")
        session.rollback()

    # 3. Minute Steps
    try:
        file_path = os.path.join(UPLOADS_DIR, "minuteStepsNarrow_merged.csv")
        if os.path.exists(file_path):
            print("Importing Minute Steps...")
            df = pd.read_csv(file_path)
            df['Id'] = df['Id'].astype(str)
            df = df[df['Id'] == primary_user_id]

            for _, row in df.iterrows():
                record = MinuteSteps(
                    user_id=row['Id'],
                    activity_minute=parse_date(row['ActivityMinute']),
                    steps=row['Steps']
                )
                session.add(record)
            session.commit()
    except Exception as e:
        print(f"Error importing Minute Steps: {e}")
        session.rollback()
        
    # 4. Sleep Log
    try:
        file_path = os.path.join(UPLOADS_DIR, "sleepDay_merged.csv")
        if os.path.exists(file_path):
            print("Importing Sleep Logs...")
            df = pd.read_csv(file_path)
            df['Id'] = df['Id'].astype(str)
            df = df[df['Id'] == primary_user_id]

            for _, row in df.iterrows():
                record = SleepLog(
                    user_id=row['Id'],
                    sleep_day=parse_date(row['SleepDay']).date(),
                    total_sleep_records=row['TotalSleepRecords'],
                    total_minutes_asleep=row['TotalMinutesAsleep'],
                    total_time_in_bed=row['TotalTimeInBed']
                )
                session.add(record)
            session.commit()
    except Exception as e:
        print(f"Error importing Sleep Logs: {e}")
        session.rollback()

    # 5. Heart Rate
    try:
        file_path = os.path.join(UPLOADS_DIR, "heartrate_seconds_merged.csv")
        if os.path.exists(file_path):
            print("Importing Heart Rate (this might take a while)...")
            df = pd.read_csv(file_path)
            df['Id'] = df['Id'].astype(str)
            df = df[df['Id'] == primary_user_id]
            
            # Batch insert for performance
            batch = []
            for _, row in df.iterrows():
                batch.append(HeartRate(
                    user_id=row['Id'],
                    time=parse_date(row['Time']),
                    value=row['Value']
                ))
                if len(batch) >= 1000:
                    session.add_all(batch)
                    session.commit()
                    batch = []
            if batch:
                session.add_all(batch)
                session.commit()
                
    except Exception as e:
        print(f"Error importing Heart Rate: {e}")
        session.rollback()

    print("Ingestion complete.")
    session.close()

if __name__ == "__main__":
    ingest_data()

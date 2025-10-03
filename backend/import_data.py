import sys
import os

sys.path.append('/opt/tcecontacts/backend')
from app.main import db_manager

# Import your Courses.csv if you have it
if os.path.exists('data/Courses.csv'):
    db_manager.import_courses_csv('data/Courses.csv')
    print("Courses imported successfully")

print("Database ready for use")

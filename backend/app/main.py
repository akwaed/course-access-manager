"""
Course Access Manager Backend API with SQLite Database
University of Kentucky - Course Access Management System
"""

import os
import json
import csv
import sqlite3
import smtplib
from datetime import datetime
from typing import List, Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException, Depends, Body, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field
import pandas as pd
import uvicorn
import bcrypt

# Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "courseaccess@uky.edu")
ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "admin@uky.edu").split(",")
DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "course_access.db"

# Fallback admin account
FALLBACK_ADMIN_USER = "admin@uky.edu"
FALLBACK_ADMIN_PASSWORD_HASH = bcrypt.hashpw(b"UK2024Admin!", bcrypt.gensalt())

app = FastAPI(
    title="Course Access Manager API",
    description="Backend API for University of Kentucky Course Access Management",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ContactType(BaseModel):
    College: str = "College"
    Department: str = "Department"
    Course: str = "Course Coordinator"

class LevelType(BaseModel):
    ReportViewer: str = "Report Viewer"
    SourceViewer: str = "Source Viewer"

class Contact(BaseModel):
    id: Optional[int] = None
    linkblue: str
    first_name: str
    last_name: str
    primary_contact: bool = False
    contact_type: str = "Department"
    college: str
    department: Optional[str] = "All"
    course: Optional[str] = None
    prefix: Optional[str] = "All"
    level_type: str = "Report Viewer"
    notes: Optional[str] = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

class PendingChange(BaseModel):
    id: Optional[int] = None
    change_type: str  # 'add', 'modify', 'delete'
    contact_id: Optional[int] = None
    data: Dict[str, Any]
    requested_by: str
    requested_at: datetime
    status: str = "pending"  # 'pending', 'approved', 'rejected'
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None

class ExportRequest(BaseModel):
    format: str = "csv"
    include_pending: bool = False
    exclude_crosslisted: bool = True

class User(BaseModel):
    email: str
    role: str  # 'System Admin', 'College Primary Contact', 'Department Contact'
    college: Optional[str] = None
    department: Optional[str] = None

# Database Management
class DatabaseManager:
    def __init__(self):
        self.init_database()
        
    @contextmanager
    def get_db(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize SQLite database with tables"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            
            # Contacts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    linkblue TEXT UNIQUE NOT NULL,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    primary_contact BOOLEAN DEFAULT FALSE,
                    contact_type TEXT NOT NULL,
                    college TEXT NOT NULL,
                    department TEXT,
                    course TEXT,
                    prefix TEXT,
                    level_type TEXT DEFAULT 'Report Viewer',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Pending changes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pending_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    change_type TEXT NOT NULL,
                    contact_id INTEGER,
                    data TEXT NOT NULL,
                    requested_by TEXT NOT NULL,
                    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    reviewed_by TEXT,
                    reviewed_at TIMESTAMP,
                    FOREIGN KEY (contact_id) REFERENCES contacts (id)
                )
            """)
            
            # Courses table (cached from CSV)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    section_key TEXT,
                    title TEXT,
                    prefix TEXT,
                    class TEXT,
                    class_id INTEGER UNIQUE,
                    class_department TEXT,
                    class_department_id INTEGER,
                    class_college TEXT,
                    class_college_short INTEGER,
                    is_crosslisted TEXT DEFAULT 'N',
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    role TEXT NOT NULL,
                    college TEXT,
                    department TEXT,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Audit log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    table_name TEXT,
                    record_id INTEGER,
                    old_values TEXT,
                    new_values TEXT,
                    user_email TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert fallback admin if not exists
            cursor.execute("""
                INSERT OR IGNORE INTO users (email, password_hash, role)
                VALUES (?, ?, 'System Admin')
            """, (FALLBACK_ADMIN_USER, FALLBACK_ADMIN_PASSWORD_HASH.decode('utf-8')))
            
            conn.commit()
    
    def get_contacts(self, active_only=True) -> List[Dict]:
        """Get all contacts from database"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM contacts"
            if active_only:
                query += " WHERE active = TRUE"
            query += " ORDER BY college, linkblue"
            
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_contact(self, contact_id: int) -> Optional[Dict]:
        """Get single contact by ID"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def add_contact(self, contact: Contact, user_email: str) -> int:
        """Add new contact to database"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            
            # Check for duplicate linkblue
            cursor.execute("SELECT id FROM contacts WHERE linkblue = ? AND active = TRUE", 
                          (contact.linkblue,))
            if cursor.fetchone():
                raise ValueError(f"Contact with LinkBlue {contact.linkblue} already exists")
            
            # Insert contact
            cursor.execute("""
                INSERT INTO contacts (
                    linkblue, first_name, last_name, primary_contact,
                    contact_type, college, department, course, prefix,
                    level_type, notes, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                contact.linkblue, contact.first_name, contact.last_name,
                contact.primary_contact, contact.contact_type, contact.college,
                contact.department, contact.course, contact.prefix,
                contact.level_type, contact.notes, user_email
            ))
            
            contact_id = cursor.lastrowid
            
            # Log action
            self.log_action(conn, 'INSERT', 'contacts', contact_id, None, 
                          contact.dict(), user_email)
            
            conn.commit()
            return contact_id
    
    def update_contact(self, contact_id: int, contact: Contact, user_email: str):
        """Update existing contact"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            
            # Get old values for audit
            old_contact = self.get_contact(contact_id)
            if not old_contact:
                raise ValueError(f"Contact {contact_id} not found")
            
            # Update contact
            cursor.execute("""
                UPDATE contacts SET
                    first_name = ?, last_name = ?, primary_contact = ?,
                    contact_type = ?, college = ?, department = ?,
                    course = ?, prefix = ?, level_type = ?, notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                contact.first_name, contact.last_name, contact.primary_contact,
                contact.contact_type, contact.college, contact.department,
                contact.course, contact.prefix, contact.level_type,
                contact.notes, contact_id
            ))
            
            # Log action
            self.log_action(conn, 'UPDATE', 'contacts', contact_id, 
                          old_contact, contact.dict(), user_email)
            
            conn.commit()
    
    def delete_contact(self, contact_id: int, user_email: str):
        """Soft delete contact (mark as inactive)"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            
            # Get old values for audit
            old_contact = self.get_contact(contact_id)
            if not old_contact:
                raise ValueError(f"Contact {contact_id} not found")
            
            # Soft delete
            cursor.execute("""
                UPDATE contacts SET active = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (contact_id,))
            
            # Log action
            self.log_action(conn, 'DELETE', 'contacts', contact_id, 
                          old_contact, None, user_email)
            
            conn.commit()
    
    def import_courses_csv(self, csv_path: str):
        """Import courses from CSV to database"""
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        with self.get_db() as conn:
            cursor = conn.cursor()
            
            # Clear existing courses
            cursor.execute("DELETE FROM courses")
            
            # Insert new courses
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO courses (
                        section_key, title, prefix, class, class_id,
                        class_department, class_department_id,
                        class_college, class_college_short, is_crosslisted
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('SECTION_KEY'), row.get('TITLE'),
                    row.get('PREFIX'), row.get('CLASS'),
                    int(row.get('CLASS_ID')) if pd.notna(row.get('CLASS_ID')) else None,
                    row.get('CLASS_DEPARTMENT'),
                    int(row.get('CLASS_DEPARTMENT_ID')) if pd.notna(row.get('CLASS_DEPARTMENT_ID')) else None,
                    row.get('CLASS_COLLEGE'),
                    int(row.get('CLASS_COLLEGE_SHORT')) if pd.notna(row.get('CLASS_COLLEGE_SHORT')) else None,
                    row.get('IS_CROSSLISTED', 'N')
                ))
            
            conn.commit()
    
    def get_courses(self) -> List[Dict]:
        """Get all courses from database"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM courses")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_pending_changes(self, status: Optional[str] = None) -> List[Dict]:
        """Get pending changes"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT * FROM pending_changes WHERE status = ?", (status,))
            else:
                cursor.execute("SELECT * FROM pending_changes")
            
            changes = []
            for row in cursor.fetchall():
                change = dict(row)
                change['data'] = json.loads(change['data'])
                changes.append(change)
            return changes
    
    def create_pending_change(self, change: PendingChange) -> int:
        """Create pending change for approval"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO pending_changes (
                    change_type, contact_id, data, requested_by
                ) VALUES (?, ?, ?, ?)
            """, (
                change.change_type, change.contact_id,
                json.dumps(change.data), change.requested_by
            ))
            conn.commit()
            return cursor.lastrowid
    
    def approve_change(self, change_id: int, reviewer: str):
        """Approve and apply pending change"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            
            # Get change
            cursor.execute("SELECT * FROM pending_changes WHERE id = ?", (change_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Change {change_id} not found")
            
            change = dict(row)
            change['data'] = json.loads(change['data'])
            
            # Apply change based on type
            if change['change_type'] == 'add':
                contact = Contact(**change['data'])
                self.add_contact(contact, reviewer)
            elif change['change_type'] == 'modify':
                contact = Contact(**change['data'])
                self.update_contact(change['contact_id'], contact, reviewer)
            elif change['change_type'] == 'delete':
                self.delete_contact(change['contact_id'], reviewer)
            
            # Update change status
            cursor.execute("""
                UPDATE pending_changes 
                SET status = 'approved', reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (reviewer, change_id))
            
            conn.commit()
    
    def log_action(self, conn, action: str, table: str, record_id: int, 
                   old_values: Any, new_values: Any, user: str):
        """Log action to audit table"""
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_log (
                action, table_name, record_id, old_values, new_values, user_email
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            action, table, record_id,
            json.dumps(old_values) if old_values else None,
            json.dumps(new_values) if new_values else None,
            user
        ))

db_manager = DatabaseManager()

# Email Service
class EmailService:
    def send_notification(self, subject: str, message: str, recipients: List[str] = None):
        """Send email notification to administrators"""
        if not recipients:
            recipients = ADMIN_EMAILS
        
        if not SMTP_HOST:
            print(f"Email notification skipped (no SMTP configured): {subject}")
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = SMTP_FROM
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"[UK Course Access Manager] {subject}"
            
            # Add UK branding to email
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="background-color: #0033A0; padding: 20px; color: white;">
                    <h2>University of Kentucky</h2>
                    <h3>Course Access Manager Notification</h3>
                </div>
                <div style="padding: 20px;">
                    {message}
                </div>
                <div style="background-color: #B1C9E8; padding: 10px; margin-top: 20px;">
                    <small>This is an automated message from the UK Course Access Manager system.</small>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                if SMTP_USER and SMTP_PASSWORD:
                    server.starttls()
                    server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
                
        except Exception as e:
            print(f"Failed to send email: {e}")

email_service = EmailService()

# Authentication
def verify_user(email: str, password: str = None) -> Optional[User]:
    """Verify user credentials"""
    # Check fallback admin
    if email == FALLBACK_ADMIN_USER:
        if password and bcrypt.checkpw(password.encode('utf-8'), FALLBACK_ADMIN_PASSWORD_HASH):
            return User(email=email, role="System Admin")
        return None
    
    # Check database users (when Azure AD is implemented)
    with db_manager.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ? AND active = TRUE", (email,))
        row = cursor.fetchone()
        if row:
            user_dict = dict(row)
            return User(
                email=user_dict['email'],
                role=user_dict['role'],
                college=user_dict.get('college'),
                department=user_dict.get('department')
            )
    
    return None

# API Routes
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "UK Course Access Manager API",
        "version": "2.0.0"
    }

@app.get("/api/contacts")
async def get_contacts(active_only: bool = True):
    """Get all contacts"""
    return db_manager.get_contacts(active_only)

@app.post("/api/contacts")
async def add_contact(contact: Contact, user: str = Query(default=FALLBACK_ADMIN_USER)):
    """Add a new contact"""
    try:
        # Check for multiple primary contacts
        if contact.primary_contact:
            existing_primary = [c for c in db_manager.get_contacts() 
                               if c['college'] == contact.college and c['primary_contact']]
            if existing_primary:
                email_service.send_notification(
                    "Multiple Primary Contacts Warning",
                    f"""
                    <p>A second primary contact has been assigned to <strong>{contact.college}</strong>:</p>
                    <ul>
                        <li>Existing: {existing_primary[0]['first_name']} {existing_primary[0]['last_name']} ({existing_primary[0]['linkblue']})</li>
                        <li>New: {contact.first_name} {contact.last_name} ({contact.linkblue})</li>
                    </ul>
                    <p>Please review this configuration.</p>
                    """
                )
        
        contact_id = db_manager.add_contact(contact, user)
        return {"message": "Contact added successfully", "id": contact_id}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding contact: {str(e)}")

@app.put("/api/contacts/{contact_id}")
async def update_contact(contact_id: int, contact: Contact, user: str = Query(default=FALLBACK_ADMIN_USER)):
    """Update an existing contact"""
    try:
        db_manager.update_contact(contact_id, contact, user)
        return {"message": "Contact updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating contact: {str(e)}")

@app.delete("/api/contacts/{contact_id}")
async def delete_contact(contact_id: int, user: str = Query(default=FALLBACK_ADMIN_USER)):
    """Delete a contact"""
    try:
        db_manager.delete_contact(contact_id, user)
        return {"message": "Contact deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting contact: {str(e)}")

@app.get("/api/courses")
async def get_courses():
    """Get all courses"""
    return db_manager.get_courses()

@app.get("/api/hierarchy")
async def get_hierarchy():
    """Get college/department/course hierarchy"""
    courses = db_manager.get_courses()
    
    hierarchy = {}
    for course in courses:
        college = course.get('class_college')
        if not college:
            continue
            
        if college not in hierarchy:
            hierarchy[college] = {
                'short': course.get('class_college_short'),
                'departments': {}
            }
        
        dept = course.get('class_department')
        if dept and dept not in hierarchy[college]['departments']:
            hierarchy[college]['departments'][dept] = {
                'id': course.get('class_department_id'),
                'prefixes': set(),
                'courses': []
            }
        
        if dept:
            prefix = course.get('prefix')
            if prefix:
                hierarchy[college]['departments'][dept]['prefixes'].add(prefix)
            
            hierarchy[college]['departments'][dept]['courses'].append({
                'class': course.get('class'),
                'class_id': course.get('class_id'),
                'prefix': prefix,
                'is_crosslisted': course.get('is_crosslisted', 'N')
            })
    
    # Convert sets to lists for JSON serialization
    for college in hierarchy.values():
        for dept in college['departments'].values():
            dept['prefixes'] = list(dept['prefixes'])
    
    return hierarchy

@app.post("/api/pending-changes")
async def create_pending_change(change: PendingChange):
    """Create a pending change for approval"""
    try:
        change_id = db_manager.create_pending_change(change)
        
        # Notify admins
        email_service.send_notification(
            "Pending Approval Required",
            f"""
            <p>A new change requires approval:</p>
            <ul>
                <li>Type: <strong>{change.change_type}</strong></li>
                <li>Requested by: {change.requested_by}</li>
                <li>Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}</li>
            </ul>
            <p><a href="https://courseaccess.uky.edu/admin/pending/{change_id}">Review Change</a></p>
            """
        )
        
        return {"message": "Change submitted for approval", "id": change_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating pending change: {str(e)}")

@app.get("/api/pending-changes")
async def get_pending_changes(status: Optional[str] = "pending"):
    """Get pending changes"""
    return db_manager.get_pending_changes(status)

@app.put("/api/pending-changes/{change_id}/approve")
async def approve_change(change_id: int, reviewer: str = Body(default=FALLBACK_ADMIN_USER)):
    """Approve a pending change"""
    try:
        db_manager.approve_change(change_id, reviewer)
        return {"message": "Change approved and applied"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error approving change: {str(e)}")

@app.post("/api/export")
async def export_data(request: ExportRequest, user: str = Query(default=FALLBACK_ADMIN_USER)):
    """Generate export file in ReportViewer format"""
    
    # Verify user is admin
    user_obj = verify_user(user)
    if not user_obj or user_obj.role != "System Admin":
        raise HTTPException(status_code=403, detail="Only System Admins can export data")
    
    contacts = db_manager.get_contacts()
    courses = db_manager.get_courses()
    
    rows = []
    
    for contact in contacts:
        target = contact['linkblue']
        
        if contact['contact_type'] == 'College':
            # College-level access
            college_short = next((c['class_college_short'] for c in courses 
                                 if c['class_college'] == contact['college']), None)
            if college_short:
                rows.append({
                    'Source': college_short,
                    'Target': target,
                    'Target_type': 'C4',
                    'blue$datablock': 'ReportViewersToUsers'
                })
        
        elif contact['contact_type'] == 'Department':
            # Department-level access
            if contact.get('department') == 'All':
                # All departments in college
                dept_ids = set(c['class_department_id'] for c in courses 
                              if c['class_college'] == contact['college'] 
                              and c['class_department_id'])
                for dept_id in dept_ids:
                    rows.append({
                        'Source': dept_id,
                        'Target': target,
                        'Target_type': 'D3',
                        'blue$datablock': 'ReportViewersToUsers'
                    })
            else:
                # Specific department
                dept_id = next((c['class_department_id'] for c in courses 
                               if c['class_department'] == contact.get('department')), None)
                if dept_id:
                    rows.append({
                        'Source': dept_id,
                        'Target': target,
                        'Target_type': 'D3',
                        'blue$datablock': 'ReportViewersToUsers'
                    })
        
        elif contact['contact_type'] == 'Course Coordinator':
            # Course-level access
            prefix = (contact.get('prefix') or '').upper()
            
            if prefix and prefix != 'ALL':
                # Prefix-level access - expand to all matching courses
                matching_courses = [c for c in courses 
                                  if (c.get('prefix', '').upper() == prefix or
                                      (c.get('class', '').replace(' ', '').upper().startswith(prefix)))
                                  and (not request.exclude_crosslisted or c.get('is_crosslisted') != 'Y')]
                
                for course in matching_courses:
                    if course.get('class_id'):
                        rows.append({
                            'Source': course['class_id'],
                            'Target': target,
                            'Target_type': 'CRS1',
                            'blue$datablock': 'ReportViewersToUsers'
                        })
            
            elif contact.get('course'):
                # Single course access
                course_match = next((c for c in courses 
                                   if c['class'] == contact['course'] or 
                                   str(c.get('class_id')) == str(contact['course'])), None)
                
                if course_match and course_match.get('class_id'):
                    rows.append({
                        'Source': course_match['class_id'],
                        'Target': target,
                        'Target_type': 'CRS1',
                        'blue$datablock': 'ReportViewersToUsers'
                    })
    
    # Create CSV
    output = "Source,Target,Target_type,blue$datablock\n"
    for row in rows:
        output += f"{row['Source']},{row['Target']},{row['Target_type']},{row['blue$datablock']}\n"
    
    # Return as streaming response
    date_str = datetime.now().strftime('%Y-%m-%d')
    filename = f"ReportViewer-{date_str}.csv"
    
    return StreamingResponse(
        iter([output]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.post("/api/upload/courses")
async def upload_courses(file: UploadFile = File(...)):
    """Upload new Courses.csv file"""
    try:
        # Save uploaded file
        temp_path = DATA_DIR / "temp_courses.csv"
        content = await file.read()
        
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        # Import to database
        db_manager.import_courses_csv(str(temp_path))
        
        # Clean up temp file
        temp_path.unlink()
        
        return {"message": "Courses file uploaded and imported successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading courses: {str(e)}")

@app.post("/api/upload/contacts")
async def upload_contacts(file: UploadFile = File(...), user: str = Query(default=FALLBACK_ADMIN_USER)):
    """Import contacts from CSV file"""
    try:
        content = await file.read()

        # Parse CSV
        import io
        csv_file = io.StringIO(content.decode('utf-8'))
        reader = csv.DictReader(csv_file)

        imported_count = 0
        skipped_count = 0
        for row in reader:
            # Skip empty rows
            if not row.get('linkblue'):
                continue

            contact = Contact(
                linkblue=row['linkblue'].strip(),
                first_name=row['first_name'].strip(),
                last_name=row['last_name'].strip(),
                primary_contact=str(row.get('primary_contact', '')).lower() in ['true', '1', 'yes'],
                contact_type=row.get('contact_type', 'Department').strip(),
                college=row['college'].strip(),
                department=row.get('department', 'All').strip() if row.get('department') else 'All',
                course=row.get('course', '').strip() if row.get('course') else None,
                prefix=row.get('prefix', 'All').strip() if row.get('prefix') else 'All',
                level_type=row.get('level_type', 'Report Viewer').strip() if row.get('level_type') else 'Report Viewer',
                notes=row.get('notes', '').strip() if row.get('notes') else ''
            )

            try:
                db_manager.add_contact(contact, user)
                imported_count += 1
            except ValueError as e:
                # Skip duplicates
                print(f"Skipping duplicate: {e}")
                skipped_count += 1
                continue

        return {
            "message": f"Imported {imported_count} contacts successfully",
            "imported": imported_count,
            "skipped": skipped_count
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing contacts: {str(e)}")

@app.get("/api/audit-log")
async def get_audit_log(limit: int = 100):
    """Get audit log entries"""
    with db_manager.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        logs = []
        for row in cursor.fetchall():
            log = dict(row)
            if log.get('old_values'):
                log['old_values'] = json.loads(log['old_values'])
            if log.get('new_values'):
                log['new_values'] = json.loads(log['new_values'])
            logs.append(log)

        return logs

@app.post("/api/generate/hierarchy")
async def generate_hierarchy_file():
    """Generate hierarchy CSV file from course data"""
    try:
        import io
        from fastapi.responses import StreamingResponse

        # Check if course.csv exists
        course_csv_path = DATA_DIR / "course.csv"
        if not course_csv_path.exists():
            raise HTTPException(status_code=404, detail="Course CSV file not found. Please upload course.csv first.")

        # Read the course.csv file
        with open(course_csv_path, 'r', encoding='utf-8') as f:
            course_data = f.read()

        # Create a StringIO object to work with the CSV
        csv_input = io.StringIO(course_data)
        reader = csv.DictReader(csv_input)

        # Prepare output CSV
        output = io.StringIO()

        # Define all expected hierarchy columns based on user's sample
        hierarchy_columns = [
            'SECTION_KEY', 'TITLE', 'CANVAS_SIS_ID', 'CRS_SECTION', 'PREFIX', 'CLASS',
            'CLASS_ID', 'SECTION', 'SECTION_ID', 'ACADEMIC_YEAR', 'ACADEMIC_TERM_ID',
            'ACADEMIC_TERM', 'SECTION_TITLE', 'SECTION_BEGIN_DATE', 'SECTION_END_DATE',
            'SECTION_LENGTH_DAYS', 'TCE_INVITE', 'TCE_R1', 'TCE_R2', 'TCE_END_DATE',
            'TCE_REPORT_DATE', 'CLASS_DEPARTMENT', 'CLASS_DEPARTMENT_ID', 'CLASS_COLLEGE',
            'CLASS_COLLEGE_SHORT', 'CLASS_LEVEL', 'IS_CROSSLISTED', 'CROSSLISTED_ID',
            'DISTANCE_LEARNING', 'IS_UK_CORE', 'UK_CORE_TYPE', 'SPEC_TYPE'
        ]

        writer = csv.DictWriter(output, fieldnames=hierarchy_columns)
        writer.writeheader()

        # Process each row and write to output
        for row in reader:
            # Create a new row with all expected columns, filling missing ones with empty strings
            hierarchy_row = {}
            for col in hierarchy_columns:
                hierarchy_row[col] = row.get(col, '')

            writer.writerow(hierarchy_row)

        # Get the CSV content
        output.seek(0)
        csv_content = output.getvalue()

        # Return as downloadable file
        return StreamingResponse(
            io.BytesIO(csv_content.encode('utf-8')),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=hierarchy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Course CSV file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating hierarchy file: {str(e)}")

@app.post("/api/auth/login")
async def login(credentials: HTTPBasicCredentials = Depends(HTTPBasic())):
    """Authenticate user (placeholder for Azure AD integration)"""
    user = verify_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "email": user.email,
        "role": user.role,
        "college": user.college,
        "department": user.department
    }

# Main entry point
if __name__ == "__main__":
    print(f"Starting UK Course Access Manager API...")
    print(f"Fallback admin: {FALLBACK_ADMIN_USER}")
    print(f"Database: {DB_PATH}")
    uvicorn.run(app, host="0.0.0.0", port=8000)

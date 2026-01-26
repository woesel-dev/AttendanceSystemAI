"""
Database models for the attendance system using Flask-SQLAlchemy.
"""
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, Table, Column, Integer, String, DateTime, Date, Time
from sqlalchemy.orm import relationship

# This will be initialized in app/__init__.py
db = SQLAlchemy()


# Association table for many-to-many relationship between Students and Classrooms
enrollment_table = Table(
    'enrollments',
    db.Model.metadata,
    Column('student_id', String(50), ForeignKey('students.id'), primary_key=True),
    Column('classroom_id', String(50), ForeignKey('classrooms.id'), primary_key=True),
    Column('enrolled_at', DateTime, default=datetime.utcnow)
)


class Student(db.Model):
    """Student model."""
    __tablename__ = 'students'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    enrollments = relationship('Classroom', secondary=enrollment_table, back_populates='students')
    attendance_records = relationship('AttendanceRecord', back_populates='student', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert student to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Student {self.id}: {self.name}>'


class Classroom(db.Model):
    """Classroom model."""
    __tablename__ = 'classrooms'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    time_window_start = Column(Time, nullable=False, default='08:00')
    time_window_end = Column(Time, nullable=False, default='18:00')
    subject = Column(String(200), nullable=True)
    department = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    students = relationship('Student', secondary=enrollment_table, back_populates='enrollments')
    attendance_records = relationship('AttendanceRecord', back_populates='classroom', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert classroom to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'time_window_start': self.time_window_start.strftime('%H:%M') if self.time_window_start else None,
            'time_window_end': self.time_window_end.strftime('%H:%M') if self.time_window_end else None,
            'subject': self.subject,
            'department': self.department,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Classroom {self.id}: {self.name}>'


class AttendanceRecord(db.Model):
    """Attendance record model."""
    __tablename__ = 'attendance_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(50), ForeignKey('students.id'), nullable=False)
    classroom_id = Column(String(50), ForeignKey('classrooms.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(String(20), nullable=False, default='present')
    ai_headcount = Column(Integer, nullable=True)  # AI detected headcount for verification
    qr_scan_count = Column(Integer, nullable=True)  # QR scan count at time of verification
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    student = relationship('Student', back_populates='attendance_records')
    classroom = relationship('Classroom', back_populates='attendance_records')
    
    def to_dict(self):
        """Convert attendance record to dictionary."""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'classroom_id': self.classroom_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'status': self.status,
            'ai_headcount': self.ai_headcount,
            'qr_scan_count': self.qr_scan_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<AttendanceRecord {self.id}: {self.student_id} in {self.classroom_id} at {self.timestamp}>'

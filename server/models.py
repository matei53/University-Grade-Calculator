from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class University(Base):
    __tablename__ = "universities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    
    users = relationship("User", back_populates="university")

class Major(Base):
    __tablename__ = "majors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    
    users = relationship("User", back_populates="major")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    university_id = Column(Integer, ForeignKey("universities.id"), nullable=True)
    major_id = Column(Integer, ForeignKey("majors.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    university = relationship("University", back_populates="users")
    major = relationship("Major", back_populates="users")
    academic_years = relationship("AcademicYear", back_populates="user", cascade="all, delete-orphan")

class AcademicYear(Base):
    __tablename__ = "academic_years"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    label = Column(String, nullable=False)
    order_index = Column(Integer, nullable=False)
    credit_requirement = Column(Integer, nullable=True)
    
    user = relationship("User", back_populates="academic_years")
    semesters = relationship("Semester", back_populates="academic_year", cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="academic_year", cascade="all, delete-orphan")

class Semester(Base):
    __tablename__ = "semesters"
    
    id = Column(Integer, primary_key=True, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False)
    label = Column(String, nullable=False)
    order_index = Column(Integer, nullable=False)
    
    academic_year = relationship("AcademicYear", back_populates="semesters")
    subjects = relationship("Subject", back_populates="semester")

class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=False)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False)
    name = Column(String, nullable=False)
    credit_value = Column(Integer, nullable=False)
    passing_grade = Column(Float, default=5.0)
    max_grade = Column(Float, default=10.0)
    
    semester = relationship("Semester", back_populates="subjects")
    academic_year = relationship("AcademicYear", back_populates="subjects")
    assessments = relationship("Assessment", back_populates="subject", cascade="all, delete-orphan")

class Assessment(Base):
    __tablename__ = "assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    name = Column(String, nullable=False)
    weight = Column(Float, nullable=False)
    max_score = Column(Float, default=10.0)
    passing_grade = Column(Float, default=5.0)
    
    subject = relationship("Subject", back_populates="assessments")
    grades = relationship("Grade", back_populates="assessment", cascade="all, delete-orphan")

class Grade(Base):
    __tablename__ = "grades"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False, unique=True)
    score = Column(Float, nullable=True)
    
    assessment = relationship("Assessment", back_populates="grades")

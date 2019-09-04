# coding: utf-8
from sqlalchemy import Column, DateTime, Float, Integer, Table, Text
from sqlalchemy.schema import FetchedValue
from sqlalchemy.sql.sqltypes import NullType
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    return db


class DocReview(db.Model):
    __tablename__ = 'doc_reviews'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    grade = db.Column(db.Integer)
    reviewkinds = db.Column(db.Text)
    source = db.Column(db.Text, nullable=False)
    url = db.Column(db.Text, nullable=False)
    doctor_id = db.Column(db.Integer)


class Doctor(db.Model):
    __tablename__ = 'doctor'

    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.Text, nullable=False)
    docinfo = db.Column(db.Text)
    url = db.Column(db.Text)
    specialist = db.Column(db.Text)
    recognition = db.Column(db.Text)
    lecture = db.Column(db.Text)
    master = db.Column(db.Text)
    otherinfo = db.Column(db.Text)
    report_count = db.Column(db.Integer, nullable=False)
    academy = db.Column(db.Text, nullable=False)
    age = db.Column(db.Integer)


# class DoctorReport(db.Model):
#     __tablename__ = 'doctor_report'
#
#     id = db.Column(db.Integer, primary_key=True)
#     docid = db.Column(db.Integer, nullable=False)
#     reportid = db.Column(db.Integer, nullable=False)


class Equipment(db.Model):
    __tablename__ = 'equipment'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)


class HosReview(db.Model):
    __tablename__ = 'hos_reviews'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    grade = db.Column(db.Integer)
    likes = db.Column(db.Integer)
    source = db.Column(db.Text, nullable=False)
    url = db.Column(db.Text, nullable=False)
    hospital_id = db.Column(db.Integer)


class Hospital(db.Model):
    __tablename__ = 'hospital'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    homepage = db.Column(db.Text)
    region = db.Column(db.Text)
    zipcode = db.Column(db.Text)
    tellnum = db.Column(db.Text)
    nursenum = db.Column(db.Integer)
    docsnum = db.Column(db.Integer)
    location = db.Column(db.Text)
    equipments = db.Column(db.Text)
    bednum = db.Column(db.Integer)
    coursename = db.Column(db.Text)
    hosroom_num = db.Column(db.Integer)
    age = db.Column(db.Integer)
    xloc = db.Column(db.Float)
    yloc = db.Column(db.Float)
    gu = db.Column(db.Text)


class Institution(db.Model):
    __tablename__ = 'institution'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    importance = db.Column(db.Integer, nullable=False)
    field_id = db.Column(db.Text, nullable=False)
    url = db.Column(db.Text)


# class Journal(db.Model):
#     __tablename__ = 'journal'
#
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.Text, nullable=False)
#     institution_id = db.Column(db.Integer)


# class Patient(db.Model):
#     __tablename__ = 'patient'
#
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.Text, nullable=False)
#     gender = db.Column(db.Text, nullable=False)
#     job = db.Column(db.Text, nullable=False)
#     symptom_id = db.Column(db.Integer)
#     region_id = db.Column(db.Integer)
#     first_matched_doctor = db.Column(db.Integer)


# class Recognition(db.Model):
#     __tablename__ = 'recognition'
#
#     id = db.Column(db.Integer, primary_key=True)
#     field = db.Column(db.Text, nullable=False)
#     semi_field = db.Column(db.Text, nullable=False)
#     institution = db.Column(db.Integer)


class Region(db.Model):
    __tablename__ = 'region'

    id = db.Column(db.Integer, primary_key=True)
    do = db.Column(db.Text, nullable=False)
    si = db.Column(db.Text, nullable=False)
    gu = db.Column(db.Text, nullable=False)

#
# class Report(db.Model):
#     __tablename__ = 'reports'
#
#     id = db.Column(db.Integer, primary_key=True)
#     kortitle = db.Column(db.Text)
#     engtitle = db.Column(db.Text)
#     writer = db.Column(db.Text, nullable=False)
#     institute = db.Column(db.Text, nullable=False)
#     abstract = db.Column(db.Text, nullable=False)
#     keywords = db.Column(db.Text)
#     reporturl = db.Column(db.Text, nullable=False)


# class Search(db.Model):
#     __tablename__ = 'search'
#
#     id = db.Column(db.Integer, primary_key=True)
#     searchsentences = db.Column(db.Text, nullable=False)
#     date = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue())


# class Specialist(db.Model):
#     __tablename__ = 'specialist'
#
#     id = db.Column(db.Integer, primary_key=True)
#     field = db.Column(db.Text, nullable=False)
#     semi_field = db.Column(db.Text, nullable=False)
#     institution = db.Column(db.Integer)
#
#
# t_sqlite_sequence = db.Table(
#     'sqlite_sequence',
#     db.Column('name', db.NullType),
#     db.Column('seq', db.NullType)
# )


# class Symptom(db.Model):
#     __tablename__ = 'symptom'
#
#     id = db.Column(db.Integer, primary_key=True)
#     first_classification = db.Column(db.Text, nullable=False)
#     second_classification = db.Column(db.Text, nullable=False)

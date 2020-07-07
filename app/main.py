from flask import Blueprint, render_template, request, redirect, url_for,flash, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.urls import *
import requests
import re
from flask import current_app
import os
import pandas as pd
import xlsxwriter
import math

main = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

@main.route('/')
def index():
    return render_template('index.html')


@main.app_errorhandler(404)
def error_page(e):
    return render_template('404.html'), 404


@main.route('/downloading')
def download():
    return render_template('download.html')


@main.route('/se')
def download_file():
    return send_file('se.xlsx', as_attachment=True, cache_timeout=0)


@main.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    emails = ''
    mess = ''
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '' or file.filename == None:
            flash('No selected file')
            # return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            flash(filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            flash('File uploaded successfully!')
            mess = 'File uploaded successfully!'
            # return send_file
            # return redirect(url_for('main.upload', filename=filename))
            emails = read_file(filename)
            domain_sorter(emails)
    return render_template('upload.html', mess=mess)


@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name = current_user.name)


@main.route('/process', methods=['GET', 'POST'])
def process():
    results = []
    results_count = 0
    if request.method == 'POST':
        choice = request.form['taskoption']
        rawtext = request.form['rawtext']
        rawtext = requests.get(rawtext).text  #urllib2.urlopen(rawtext)
        if choice == 'email':
            # rawtext = request.form['rawtext']
            results = email_regex(rawtext)
            # results_count = len(results)
        elif choice == 'phone':
            # rawtext = request.form['rawtext']
            results = phone_regex(rawtext)
            # results_count = len(results)
        # elif choice == 'url_https':
        #     # rawtext = request.form['rawtext']
        #     results = url_https_regex(rawtext)
        #     # results_count = len(results)
        # elif choice == 'url_http':
        #     # rawtext = request.form['rawtext']
        #     results = url_http(rawtext)
            # results_count = len(results)
        results_count = len(results)
    return render_template('profile.html', results=results, results_count=results_count)


def email_regex(file):
    return re.compile(r'[\w\.-]+@[\w\.-]+').findall(file)


def phone_regex(file):
    return re.compile(r'\d\d\d. \d\d\d\.\d\d\d\d').findall(file)


def url_https_regex(file):
    return re.compile(r'https?://www\.?\w+\.\w+').findall(file)


def url_http_regex(file):
    return re.compile(r'http?://www\.?\w+\.\w+').findall(file)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_res(choice):
    if choice == 'email':
        rawtext = request.form['rawtext']
        results = email_regex.findall(rawtext)
        results_count = len(results)
    return results, results_count


def read_file(filename):
    f = open('app/'+filename,'r')
    emails = f.read().splitlines()
    f.close()
    return emails


def save_to_excel(domain_email_list):

    '''
        convert domain_email_list to a dataframe and save to excel spreadsheet
    '''


    workbook = xlsxwriter.Workbook('app/se.xlsx')
    worksheet = workbook.add_worksheet()

    # Start from the first cell.
    # Rows and columns are zero indexed.
    row = 0
    column = 0

    flag = 0

    for domain in domain_email_list.keys():
        c = math.ceil(len(max(domain_email_list[domain], key=len)) / 9) # average character per cell is 9

        cell_format = workbook.add_format({'bold': True, 'font_color': 'red'})
        worksheet.write(row, column, domain, cell_format)

        row += 1
        flag += c

        for email in domain_email_list[domain]:
            worksheet.write(row, column, email)
            row += 1
        row = 0
        column = flag

    workbook.close()
    # return workbook


def domain_sorter(emails):
    '''
        sort emails into different doamains available on the email list
    '''
    domain_list = []
    for email in emails:
        if (email.split('@')[1]) not in domain_list:
            domain_list.append(email.split('@')[1])

    # create a dictionary with domain name as key and value of an empty list
    domain_email_list = {}

    for domain in domain_list:
        if domain not in domain_email_list:
            domain_email_list[domain] = []

    # assisgn email to the domain key list
    for email in emails:
        domain_email_list[email.split('@')[1]].append(email)

    save_to_excel(domain_email_list)

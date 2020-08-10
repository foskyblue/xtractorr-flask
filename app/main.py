# https://www.wpbeginner.com/beginners-guide/how-to-setup-a-professional-email-address-with-gmail-and-google-apps/
# https://en.wikipedia.org/wiki/Email_address?

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
from bs4 import BeautifulSoup

main = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


@main.route('/')
def index():
    return render_template('index.html')


@main.app_errorhandler(400)
def error_page(e):
    return render_template('error_pages/400.html'), 400


@main.app_errorhandler(404)
def error_page(e):
    return render_template('error_pages/404.html'), 404


@main.route('/downloading')
def download():
    return render_template('download.html')


@main.route('/sorted_emails')
def download_file():
    return send_file('sorted_emails.xlsx', as_attachment=True, cache_timeout=0)


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

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            flash(filename)
            file.filename = 'uploaded_emails'

            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename))
            flash('File uploaded successfully!')
            mess = 'File uploaded successfully!'
            # return send_file
            # return redirect(url_for('main.upload', filename=filename))
            emails = read_file(file.filename)
            emails = email_regex(str(emails))
            emails_temp_list = []
            for email in emails:
                emails_temp_list.append(email[1:])
            domain_sorter(emails_temp_list)
    return render_template('upload.html', mess=mess)


@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name = current_user.name)


@main.route('/sorter', methods=['GET', 'POST'])
@login_required
def sorter():

    domain_email_dict = {}
    domains = []
    domain_count = 0
    all_emails = []
    # emails = ''
    if request.method == 'POST':

        if 'form1' in request.form:

            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '' or file.filename == None:
                flash('No selected file')

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                flash(filename)
                file.filename = 'uploaded_emails'

                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename))
                flash('File uploaded successfully!')
                mess = 'File uploaded successfully!'
                # return send_file
                # return redirect(url_for('main.upload', filename=filename))
                emails = read_file(file.filename)
                emails = email_regex(str(emails))
                emails_temp_list = []
                for email in emails:
                    emails_temp_list.append(email[1:])
                # domain_sorter(emails_temp_list)
                domain_email_dict = domain_sorter(emails_temp_list)

                domains = sorted(domain_email_dict.keys())
                domain_count = len(domains)

                for key in domain_email_dict.keys():
                    for email in domain_email_dict[key]:
                        all_emails.append(email)

                save_to_txt(all_emails, domains, domain_count, len(all_emails))

        # choice = request.form['taskoption']
        rawtext = request.form['rawtext']
        # rawtext = requests.get(rawtext).text  #urllib2.urlopen(rawtext)

        emails = email_regex(rawtext)

        domain_email_dict = domain_sorter(emails)

        domains = sorted(domain_email_dict.keys())
        domain_count = len(domains)

        for key in domain_email_dict.keys():
            for email in domain_email_dict[key]:
                all_emails.append(email)

        save_to_txt(all_emails, domains, domain_count, len(all_emails))


    return render_template('sorter.html', domains=domains, domain_count=domain_count, emails_count=len(all_emails), all_emails=all_emails)
    # return render_template('sorter.html')


@main.route('/exclude', methods=['GET', 'POST'])
@login_required
def exclude():

    all_emails = read_file('saved_emails.txt')
    domains = read_file('saved_emails_domains.txt')
    domain_count = read_file('saved_domain_count.txt')
    emails_count = read_file('saved_email_count.txt')
    domain_count = int(domain_count[0])
    emails_count = int(emails_count[0])
    checkbox_options = []
    all_emails_temp = []
    all_emails = domain_sorter(all_emails)

    if request.method == 'POST':

        checkbox_options.append(request.form.getlist('check'))
        checkbox_options = checkbox_options[0]

        for option in checkbox_options:

            if option in all_emails.keys():

                del all_emails[option]
                domains.remove(option)
                domain_count -= 1


        for key in all_emails.keys():

            for email in all_emails[key]:

                all_emails_temp.append(email)

        save_to_txt(all_emails_temp, domains, domain_count, len(all_emails))

    return render_template('sorter.html', domains=domains, domain_count=domain_count, emails_count=len(all_emails_temp), all_emails=all_emails_temp, checkbox_options=checkbox_options)


@main.route('/process', methods=['GET', 'POST'])
def process():
    results = []
    results_count = 0
    rawtext = []
    parsed_pages = 0
    domain_count = 0
    page_title = []
    webpage_link = []
    fetched_pages_in_q = 0
    if request.method == 'POST':
        choice = request.form['taskoption']
        rawtext = request.form['rawtext']
        # rawtext = requests.get(rawtext).text  #urllib2.urlopen(rawtext)
        rawtext = rawtext.split(',') # 1
        parsed_pages += len(rawtext)
        if choice == 'email':
            # rawtext = request.form['rawtext']
            # depth = 0
            for web_link in rawtext:

                # depth += 1
                web_link_q = []
                depth = 0
                web_link_q.append(web_link)
                fetched_pages_in_q += 1
                weblink_cache = []
                while len(web_link_q) != 0 and depth < 15:
                    wll = web_link_q.pop(0)
                    fetched_pages_in_q += 1
                    parsed_pages += 1
                    weblink_cache.append(wll)

                    # proxySetting = {'https' : <host>:<port>}
                    headers = {'User-Agent': 'Mozilla/5.0'}
                    page = requests.get(wll, headers=headers, verify=False) # Sucuri WebSite Firewall - Access Denied python request solution
                    # print(page)
                    soup = BeautifulSoup(page.text, 'html.parser')

                    with open('app/html_contents.html', 'w', encoding='utf-8') as f:
                        f.write(str(soup))

                    wl = read_file('html_contents.html')

                    # wl = requests.get(wl).text

                    for link in url_https_regex(str(wl)):
                        if link not in weblink_cache:
                            web_link_q.append(link)

                    for link in url_http_regex(str(wl)):
                        if link not in weblink_cache:
                            web_link_q.append(link)

                    for email in email_regex(str(wl)):
                        if email not in results:
                            results.append(email)
                            webpage_link.append(wll)
                            page_title.append(soup.find('title').text)

                    domain_count = domain_sorter(results)
                    depth += 1
                    fetched_pages_in_q += len(web_link_q)
            # results_count = len(results)
        elif choice == 'phone':
            # rawtext = request.form['rawtext']
            results = phone_regex(rawtext)

    return render_template('profile.html', rawtext=len(rawtext), results=results, fetched_pages_in_q=fetched_pages_in_q, webpage_link=webpage_link, page_title=page_title, results_count=len(results), parsed_pages=parsed_pages, domain_count=len(domain_count))


def email_regex(file):

    return re.compile(r'[\w\.-]+@[\w\.-]+').findall(file)


def phone_regex(file):
    return re.compile(r'\d\d\d. \d\d\d\.\d\d\d\d').findall(file)


def url_https_regex(file):
    return re.compile(r'https?://www\.?\w+\.\w+.\w+').findall(file)


def url_http_regex(file):
    return re.compile(r'http?://www\.?\w+\.\w+.\w+').findall(file)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_res(choice):
    if choice == 'email':
        rawtext = request.form['rawtext']
        results = email_regex.findall(rawtext)
        results_count = len(results)
    return results, results_count


def read_file(filename):
    f = open('app/'+filename, encoding="utf8")
    emails = f.read().splitlines()
    f.close()
    return emails


def save_to_excel(domain_email_list):

    '''
        convert domain_email_list to a dataframe and save to excel spreadsheet
    '''


    workbook = xlsxwriter.Workbook('app/sorted_emails.xlsx')
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

# domains=domains, domain_count=domain_count, emails_count=len(all_emails), all_emails=all_emails
def save_to_txt(emails, domains, domain_count, email_count):
    with open('app/saved_emails.txt', "w", encoding='utf-8') as myfile:
        for email in emails:
                myfile.write("%s\n" % email)

    with open('app/saved_emails_domains.txt', "w", encoding='utf-8') as myfile2:
        for domain in domains:
                myfile2.write("%s\n" % domain)

    with open('app/saved_domain_count.txt', "w", encoding='utf-8') as myfile3:
        myfile3.write("%s\n" % domain_count)

    with open('app/saved_email_count.txt', "w", encoding='utf-8') as myfile4:
        myfile4.write("%s\n" % email_count)


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

    # if caller == 'upload':
    #     save_to_excel(domain_email_list)
    # else:
    return domain_email_list

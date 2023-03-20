# pylint: disable=all
import os
from flask import Flask, render_template, request, redirect, jsonify, session, url_for

# from flask.ext.jsonpify import jsonify
from flask_mysqldb import MySQL
import yaml
from enum import Enum
from authlib.integrations.flask_client import OAuth
import json


class Occupation(Enum):
    STUDENT = 1
    CDS_EMPLOYEE = 2
    COMPANY_POC = 3

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Temporary hain, until we get the student id by session or login shit
global student_id
student_id = 1

USER = Occupation.STUDENT

app = Flask(__name__)
app.secret_key = 'nvsiunvsidnsdnvnvi'
app.config['SERVER_NAME'] = 'localhost:5000'

# Configure db
db = yaml.safe_load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

mysql = MySQL(app)
oauth = OAuth(app)
@app.route('/google')
def google():   
    # Google Oauth Config
    # Get client_id and client_secret from environment variables
    # For developement purpose you can directly put it
    # here inside double quotes
    GOOGLE_CLIENT_ID = '515566156695-um1sos28i4a2ftr37eaot6l4clvlovjs.apps.googleusercontent.com'
    GOOGLE_CLIENT_SECRET = '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'

    CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url=CONF_URL,
        client_kwargs={
            'scope': 'openid email profile',
        }
    )

    # Redirect to google_auth function
    redirect_uri = url_for('google_auth', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/google_auth')
def google_auth():
    token = oauth.google.authorize_access_token()
    session['email'] = token["userinfo"]["email"]
    email = token["userinfo"]["email"]
    cur = mysql.connection.cursor()
    resultvalue = cur.execute("SELECT student_id FROM student where student_email_id = '"+email+"';")

    if resultvalue==0:
        resultvalue = cur.execute(f"SELECT poc_email_id FROM point_of_contact where poc_email_id = '{email}';")
        if resultvalue==0:
            cur.close()
            session.clear()
            return jsonify({"error": "Invalid Access, contact Saumil Shah"}), 200
        else:
            session['occupation']='poc'
    else:
        resultvalue = cur.fetchall()[0][0]
        session['occupation']='student'
        session['student_id']=resultvalue

    cur.close()

    return redirect(url_for(session['url']))

@app.route('/logout')
def logout():
    session.clear()
    return 'You have been logged out.'


@app.route('/', methods=['GET', 'POST'])
def index():
    if not ('email' in session ):
        session['url'] = 'index'
        return redirect(url_for('google'))
    USER = session['occupation']
    match USER:
        case 'student':
            USER = Occupation.STUDENT
        case 'poc':
            USER = Occupation.COMPANY_POC
    if(USER ==Occupation.STUDENT ):
        student_id = session['student_id']

    if request.method == 'POST':
        # Fetch form data
        userDetails = request.form
        name = userDetails['name']
        email = userDetails['email']
        cur = mysql.connection.cursor()
        # cur.execute("INSERT INTO users(name, email) VALUES(%s, %s)",(name, email))
        mysql.connection.commit()
        cur.close()
        return redirect('/tables')
    return render_template('index.html')


##### for student get requests#####


@app.route('/api/opportunities', methods=['GET'])
def get_opportunities():
    # we need to check if the user is a student or not
    if not ('email' in session ):
        session['url'] = 'index'
        return redirect(url_for('google'))
    USER = session['occupation']
    match USER:
        case 'student':
            USER = Occupation.STUDENT
        case 'poc':
            USER = Occupation.COMPANY_POC
    if(USER == Occupation.STUDENT):
        student_id = session['student_id']
        print(student_id)

    if (USER != Occupation.STUDENT):
        return jsonify({"error": "Invalid Access"}), 404

    # get the student id and status from the request, request will be like: /opportunities?student_id=1&status=applied

    status = request.args.get('status')
    opp_id = request.args.get('opp_id')

    # if both student_id and status are not present, return all opportunities with their requirements
    # TO DO: add check for active opportunities
    if status is None and opp_id is None:
        cur = mysql.connection.cursor()

        # we execute the query
        resultValue = cur.execute(
            "SELECT * FROM opportunity INNER JOIN requirements ON opportunity.opp_id = requirements.opp_id;")

        # get the field names(columns) of the query
        field_names = [i[0] for i in cur.description]

        # if the query returns any results, we fetch all the results as a list of tuples and store it in opportunities
        if resultValue > 0:

            # fetch all the results as a list of tuples and store it in opportunities
            opportunities = cur.fetchall()

            # below code segment is to convert the list of tuples to a list of dictionaries
            final_opportunities = []
            for j in range(len(opportunities)):
                dict = {}
                for i in range(len(cur.description)):
                    dict[field_names[i]] = opportunities[j][i]
                final_opportunities.append(dict)

            # return the list of dictionaries as json response
            return jsonify(final_opportunities)

    # if any both queried values are present, return the opportunities with the queried status
    elif status is not None and opp_id is None:
        # similar process as in the above if block is followed based on the conditions specified in the query
        cur = mysql.connection.cursor()
        if status == 'applied':
            query = "select * from selection_procedure where opp_id in (select opp_id from app_opp where student_id = %s)"
            resultValue = cur.execute(query, (student_id,))
            field_names = [i[0] for i in cur.description]
            if resultValue > 0:
                opportunities = cur.fetchall()
                final_opportunities = []
                for j in range(len(opportunities)):
                    dict = {}
                    for i in range(len(cur.description)):
                        dict[field_names[i]] = opportunities[j][i]
                    final_opportunities.append(dict)
                return jsonify(final_opportunities)
        elif status == 'rejected' or status == 'all' or status == 'accepted':
            query = "select * from opportunity"
            resultValue = cur.execute(query)
            field_names = [i[0] for i in cur.description]
            if resultValue > 0:
                opportunities = cur.fetchall()
                final_opportunities = []
                for j in range(len(opportunities)):
                    dict = {}
                    for i in range(len(cur.description)):
                        dict[field_names[i]] = opportunities[j][i]
                    final_opportunities.append(dict)
                return jsonify(final_opportunities)
        else:
            return jsonify({"error": "invalid status"}), 404
    elif opp_id is not None and status is None:
        cur = mysql.connection.cursor()
        resultValue = cur.execute(
        "SELECT * FROM opportunity INNER JOIN requirements ON opportunity.opp_id = requirements.opp_id where opportunity.opp_id = %s", (opp_id,))
        field_names = [i[0] for i in cur.description]
        if resultValue > 0:
            opportunity_desc = cur.fetchone()
            dict = {}
            for i in range(len(cur.description)):
                dict[field_names[i]] = opportunity_desc[i]
        return jsonify(dict)

    return jsonify("No matches were found for your search criteria")

# @app.route('/api/opportunities', methods=['GET'])
# def get_opportunity_by_id():
#     if not ('email' in session ):
#         session['url'] = 'index'
#         return redirect(url_for('google'))
#     USER = session['occupation']
#     match USER:
#         case 'student':
#             USER = Occupation.STUDENT
#         case 'poc':
#             USER = Occupation.COMPANY_POC
#     if(USER == Occupation.STUDENT):
#         student_id = session['student_id']
        
#     if(USER != Occupation.STUDENT):
#         return jsonify({"error": "Invalid Accesss"}), 404
#     opp_id = request.args.get('opp_id')
#     cur = mysql.connection.cursor()
#     resultValue = cur.execute(
#         "SELECT * FROM opportunity INNER JOIN requirements ON opportunity.opp_id = requirements.opp_id where opportunity.opp_id = %s", (opp_id,))
#     field_names = [i[0] for i in cur.description]
#     if resultValue > 0:
#         opportunity_desc = cur.fetchone()
#         dict = {}
#         for i in range(len(cur.description)):
#             dict[field_names[i]] = opportunity_desc[i]
#         return jsonify(dict)
#     return jsonify("No matches were found for your search criteria")


@app.route('/api/cds/opportunity', methods=['POST'])
def add_new_opportunity():
    if not ('email' in session ):
        session['url'] = 'index'
        return redirect(url_for('google'))
    USER = session['occupation']
    match USER:
        case 'student':
            USER = Occupation.STUDENT
        case 'poc':
            USER = Occupation.COMPANY_POC
    if(USER == Occupation.STUDENT):
        student_id = session['student_id']

    if USER != Occupation.CDS_EMPLOYEE:
        return jsonify({"error": "Invalid Access"}), 404

    opportunity = request.get_json()
    # Columns in opportunity table
    # opportunity (opp_type, opp_title, address_line_1, address_line_2, address_line_3, company_id)
    opp_type = opportunity['opp_type']
    opp_title = opportunity['opp_title']
    address_line_1 = opportunity['address_line_1']
    address_line_2 = opportunity['address_line_2']
    address_line_3 = opportunity['address_line_3']
    company_id = opportunity['company_id']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO opportunity(opp_type, opp_title, address_line_1, address_line_2, address_line_3, company_id) VALUES(%s, %s, %s, %s, %s, %s)",
                (opp_type, opp_title, address_line_1, address_line_2, address_line_3, company_id))
    mysql.connection.commit()
    cur.close()
    return jsonify({"message": "Opportunity added successfully"}), 200

@app.route('/api/cds/requirements', methods=['POST'])
def add_requirements():
    if not ('email' in session ):
        session['url'] = 'index'
        return redirect(url_for('google'))
    USER = session['occupation']
    match USER:
        case 'student':
            USER = Occupation.STUDENT
        case 'poc':
            USER = Occupation.COMPANY_POC
    if(USER == Occupation.STUDENT):
        student_id = session['student_id']

    if USER != Occupation.CDS_EMPLOYEE:
        return jsonify({"error": "Invalid Access"}), 404
    requirements = request.get_json()
    # Columns in requirements table
    # Requirements: opp_id, min_cpi_req, active_backlog, program_req, dept_req, year_req, salary, opp_status, opp_req, posted_on, deadline
    opp_id = requirements['opp_id']
    min_cpi_req = requirements['min_cpi_req']
    active_backlog = requirements['active_backlog']
    program_req = requirements['program_req']
    dept_req = requirements['dept_req']
    year_req = requirements['year_req']
    salary = requirements['salary']
    opp_status = requirements['opp_status']
    opp_req = requirements['opp_req']
    posted_on = requirements['posted_on']
    deadline = requirements['deadline']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO requirements(opp_id, min_cpi_req, active_backlog, program_req, dept_req, year_req, salary, opp_status, opp_req, posted_on, deadline) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (opp_id, min_cpi_req, active_backlog, program_req, dept_req, year_req, salary, opp_status, opp_req, posted_on, deadline))
    mysql.connection.commit()
    cur.close()
    return jsonify({"message": "Requirements added successfully"}), 200

@app.route('/api/cds/opportunity_delete', methods=['POST'])
def delete_opportunity():
    if not ('email' in session ):
        session['url'] = 'index'
        return redirect(url_for('google'))
    USER = session['occupation']
    match USER:
        case 'student':
            USER = Occupation.STUDENT
        case 'poc':
            USER = Occupation.COMPANY_POC
    if(USER == Occupation.STUDENT):
        student_id = session['student_id']

    if USER != Occupation.CDS_EMPLOYEE:
        return jsonify({"error": "Invalid Access"}), 404
    opportunity = request.get_json()
    opp_id = opportunity['opp_id']
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM opportunity WHERE opp_id = %s", (opp_id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({"message": "Opportunity deleted successfully"}), 200

@app.route('/api/student/apply/', methods=['POST'])
def apply():
    if not ('email' in session ):
        session['url'] = 'index'
        return redirect(url_for('google'))
    USER = session['occupation']
    match USER:
        case 'student':
            USER = Occupation.STUDENT
        case 'poc':
            USER = Occupation.COMPANY_POC
    if(USER == Occupation.STUDENT):
        student_id = session['student_id']

    if USER != Occupation.STUDENT:
        return jsonify({"error": "Invalid Access"}), 404
    opportunity = request.get_json()
    resume_id = opportunity['resume_id']
    opp_id = opportunity['opp_id']
    cur = mysql.connection.cursor()
    cur.execute(f"INSERT INTO app_opp(student_id, opp_id, resume_id,OPP__ID,round_number_reached) VALUES({student_id}, {opp_id}, {resume_id}, {opp_id}, 1)")
    mysql.connection.commit()
    cur.close()
    return jsonify({"message": "applied successfully"}), 200

@app.route('/api/poc/opportunity', methods=['POST'])
def poc_opp():
    if not ('email' in session ):
        session['url'] = 'index'
        return redirect(url_for('google'))
    USER = session['occupation']
    match USER:
        case 'student':
            USER = Occupation.STUDENT
        case 'poc':
            USER = Occupation.COMPANY_POC
    if(USER == Occupation.STUDENT):
        student_id = session['student_id']

    if USER != Occupation.STUDENT:
        return jsonify({"error": "Invalid Access"}), 404
    opportunity = request.get_json()
    resume_id = opportunity['student_id']
    opp_id = opportunity['opp_id']
    round_number = opportunity['round_numbr']
    todo = opportunity['todo']
    cur = mysql.connection.cursor()
    cur.execute(f"INSERT INTO app_opp(student_id, opp_id, resume_id,OPP__ID,round_number_reached,status) VALUES({student_id}, {opp_id}, {resume_id}, {opp_id}, 1, 'eligible')")
    mysql.connection.commit()
    cur.close()
    return jsonify({"message": "Opportunity deleted successfully"}), 200


@app.route('/api/student/resume', methods=['POST'])
def upload_resume():
    if not ('email' in session ):
        session['url'] = 'index'
        return redirect(url_for('google'))
    USER = session['occupation']
    match USER:
        case 'student':
            USER = Occupation.STUDENT
        case 'poc':
            USER = Occupation.COMPANY_POC
    if(USER == Occupation.STUDENT):
        student_id = session['student_id']
        
    if USER != Occupation.STUDENT:
        return jsonify({"error": "Invalid Access"}), 404
    resume = request.get_json()

    # Format resume (resume_id, resume_file VARCHAR(255) CHECK (resume_file REGEXP '^(http|https)://.+'), resume_file_name);
    resume_file = resume['resume_file_link']
    resume_file_name = resume['resume_file_name']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO resume(resume_file, resume_file_name) VALUES(%s, %s);",
                (resume_file, resume_file_name))
    mysql.connection.commit()
    cur.close()
    cur = mysql.connection.cursor()
    
    resume_id = cur.execute("select * from resume where resume_file='" + resume_file + "' and resume_file_name='"+resume_file_name+"';")
    resume_id = cur.fetchall()[0][0]
    # print(f"INSERT INTO app_opp(student_id, resume_id) VALUES(%s, %s)", (student_id, resume_id))
    print("select resume_id from resume where resume_file='" + resume_file + "' and resume_file_name='"+resume_file_name+"'")
    print(resume_id)
    cur.execute("INSERT INTO app_opp(student_id, resume_id) VALUES(%s, %s);", (student_id, resume_id))
    mysql.connection.commit()
    cur.close()
    return jsonify({"message": "Resume uploaded successfully"}), 200


@app.route('/api/student/image', methods=['POST'])
def upload_image():
    if not ('email' in session ):
        session['url'] = 'index'
        return redirect(url_for('google'))
    USER = session['occupation']
    match USER:
        case 'student':
            USER = Occupation.STUDENT
        case 'poc':
            USER = Occupation.COMPANY_POC
    if(USER == Occupation.STUDENT):
        student_id = session['student_id']
        
    if USER != Occupation.STUDENT:
        return jsonify({"error": "Invalid Access"}), 404
    image = request.get_json()
    # Format student (studentid, student_image)
    id = student_id
    student_image = image['student_image']
    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE student SET student_image = %s WHERE student_id = %s", (student_image, id))
    mysql.connection.commit()
    cur.close()
    return jsonify({"message": "Image uploaded successfully"}), 200



    
@app.route('/api/student', methods=['GET'])
def get_student_by_id():
    if not ('email' in session ):
        session['url'] = 'index'
        return redirect(url_for('google'))
    USER = session['occupation']
    match USER:
        case 'student':
            USER = Occupation.STUDENT
        case 'poc':
            USER = Occupation.COMPANY_POC
    if(USER == Occupation.STUDENT):
        student_id = session['student_id']

    if (USER != Occupation.STUDENT):
        return jsonify({"error": "Invalid Access"}), 404
    cur = mysql.connection.cursor()
    resultValue = cur.execute(
        "select * from student where student_id = %s", (student_id,))
    field_names = [i[0] for i in cur.description]
    if resultValue > 0:
        student_desc = cur.fetchone()
        dict = {}
        for i in range(len(cur.description)):
            dict[field_names[i]] = student_desc[i]

        return jsonify(dict) 
    return jsonify("No matches were found for your search criteria")

@app.route('/api/student/resume', methods=['GET'])
def get_resume_by_id():
    if not ('email' in session ):
        session['url'] = 'index'
        return redirect(url_for('google'))
    USER = session['occupation']
    match USER:
        case 'student':
            USER = Occupation.STUDENT
        case 'poc':
            USER = Occupation.COMPANY_POC
    if(USER == Occupation.STUDENT):
        student_id = session['student_id']

    if (USER != Occupation.STUDENT):
        return jsonify({"error": "Invalid Access"}), 404
    cur = mysql.connection.cursor()
    resultValue = cur.execute(
        "select * from resume where resume_id in (select resume_id from app_opp where student_id = %s)", (student_id,))
    field_names = [i[0] for i in cur.description]
    if resultValue > 0:
        res_desc = cur.fetchall()
        final_list = []
        for j in range(len(res_desc)):
            dict = {}
            for i in range(len(cur.description)):
                dict[field_names[i]] = res_desc[j][i]
            final_list.append(dict)
        return jsonify(final_list)
    return jsonify("No matches were found for your search criteria")

@app.route('/student/opportunities/applied', methods=['GET'])
def applied_list():
    if not ('email' in session ):
        session['url'] = 'index'
        return redirect(url_for('google'))
    USER = session['occupation']
    match USER:
        case 'student':
            USER = Occupation.STUDENT
        case 'poc':
            USER = Occupation.COMPANY_POC
    if(USER == Occupation.STUDENT):
        student_id = session['student_id']
    return render_template('student_pages/applied_details.html')



##### for POC get requests#####

@app.route('/poc/opportunity', methods=['GET'])
def get_opportunity_by_id_for_poc():
    if not ('email' in session ):
        session['url'] = 'index'
        return redirect(url_for('google'))
    USER = session['occupation']
    match USER:
        case 'student':
            USER = Occupation.STUDENT
        case 'poc':
            USER = Occupation.COMPANY_POC
    if(USER == Occupation.STUDENT):
        student_id = session['student_id']

    if (USER != Occupation.COMPANY_POC):
        return jsonify({"error": "Invalid Access"}), 404
    poc_email_id = request.args.get('poc_email_id')
    cur = mysql.connection.cursor()
    query = "SELECT * FROM opportunity INNER JOIN requirements ON opportunity.opp_id = requirements.opp_id WHERE opportunity.opp_id in (select opp_id from point_of_contact where poc_email_id = %s);"
    resultValue = cur.execute(query,(poc_email_id,))
    field_names = [i[0] for i in cur.description]
    if resultValue > 0:
        opportunities = cur.fetchall()
        final_opportunities = []
        for j in range(len(opportunities)):
            dict = {}
            for i in range(len(cur.description)):
                if field_names[i] == "min_cpi_req":
                    dict[field_names[i]] = float(opportunities[j][i])
                else: dict[field_names[i]] = opportunities[j][i]
            final_opportunities.append(dict)

        # return the list of dictionaries as json response
        return jsonify(final_opportunities)
    return jsonify("No matches were found for your search criteria")


@app.route('/poc/opportunity/student', methods=['GET'])
def get_opportunity_by_id_and_round_no_for_poc():
    if not ('email' in session ):
        session['url'] = 'index'
        return redirect(url_for('google'))
    USER = session['occupation']
    match USER:
        case 'student':
            USER = Occupation.STUDENT
        case 'poc':
            USER = Occupation.COMPANY_POC
    if(USER == Occupation.STUDENT):
        student_id = session['student_id']

    if (USER != Occupation.COMPANY_POC):
        return jsonify({"error": "Invalid Access"}), 404
    opp_id = request.args.get('opp_id')
    round_number = request.args.get('round_number')
    cur = mysql.connection.cursor()
    query = "SELECT * FROM student WHERE student.student_id in (SELECT s.student_id FROM student s JOIN application a ON s.student_id = a.student_id JOIN app_opp ao ON a.student_id = ao.student_id AND a.opp_id = ao.opp_id AND a.resume_id = ao.resume_id JOIN selection_procedure sp ON ao.OPP__ID = sp.opp_id WHERE sp.opp_id = %s AND sp.round_number >= %s);"
    resultValue = cur.execute(query,(opp_id,round_number))
    field_names = [i[0] for i in cur.description]
    if resultValue > 0:
        students = cur.fetchall()
        final_students = []
        for j in range(len(students)):
            dict = {}
            for i in range(len(cur.description)):
                if field_names[i] == 'CPI': dict[field_names[i]] = float(students[j][i])
                else: dict[field_names[i]] = students[j][i]
            final_students.append(dict)

        # return the list of dictionaries as json response
        return jsonify(final_students)
    return jsonify("No matches were found for your search criteria")


@app.route('/opportunity/selected', methods=['GET'])
def get_student_details_by_opportunity_id():
    if not ('email' in session ):
        session['url'] = 'index'
        return redirect(url_for('google'))
    USER = session['occupation']
    match USER:
        case 'student':
            USER = Occupation.STUDENT
        case 'poc':
            USER = Occupation.COMPANY_POC
    if(USER == Occupation.STUDENT):
        student_id = session['student_id']

    if (USER != Occupation.COMPANY_POC and USER != Occupation.CDS_EMPLOYEE):
        return jsonify({"error": "Invalid Access"}), 404
    opp_id = request.args.get('opp_id')
    cur = mysql.connection.cursor()
    query = "SELECT * FROM student WHERE student.student_id in (SELECT application.student_id FROM application WHERE application.opp_id = %s);"
    resultValue = cur.execute(query,(opp_id,))
    field_names = [i[0] for i in cur.description]
    if resultValue > 0:
        students = cur.fetchall()
        final_students = []
        for j in range(len(students)):
            dict = {}
            for i in range(len(cur.description)):
                if field_names[i] == 'CPI': dict[field_names[i]] = float(students[j][i])
                else: dict[field_names[i]] = students[j][i]
            final_students.append(dict)
        # return the list of dictionaries as json response
        return jsonify(final_students)
    return jsonify("No matches were found for your search criteria")

@app.route('/cds/opportunity', methods=['GET'])
def get_opportunity_by_id_for_cds_and_poc():
    if not ('email' in session ):
        session['url'] = 'index'
        return redirect(url_for('google'))
    USER = session['occupation']
    match USER:
        case 'student':
            USER = Occupation.STUDENT
        case 'poc':
            USER = Occupation.COMPANY_POC
    if(USER == Occupation.STUDENT):
        student_id = session['student_id']

    if(USER != Occupation.CDS_EMPLOYEE and USER != Occupation.COMPANY_POC):
        return jsonify({"error": "Invalid Accesss"}), 404
    opp_id = request.args.get('opp_id')
    cur = mysql.connection.cursor()
    resultValue = cur.execute(
        "SELECT * FROM opportunity INNER JOIN requirements ON opportunity.opp_id = requirements.opp_id where opportunity.opp_id = %s", (opp_id,))
    field_names = [i[0] for i in cur.description]
    if resultValue > 0:
        opportunuities = cur.fetchall()
        final_opportunuities = []
        for j in range(len(opportunuities)):
            dict = {}
            for i in range(len(cur.description)):
                if field_names[i] == 'min_cpi_req': 
                    dict[field_names[i]] = float(opportunuities[j][i])
                else :
                    dict[field_names[i]] = opportunuities[j][i]
            final_opportunuities.append(dict)
        # return the list of dictionaries as json response
        return jsonify(final_opportunuities)
    return jsonify("No matches were found for your search criteria")

@app.route('/poc')
def poc():
    if not ('email' in session ):
        session['url'] = 'index'
        return redirect(url_for('google'))
    USER = session['occupation']
    match USER:
        case 'student':
            USER = Occupation.STUDENT
        case 'poc':
            USER = Occupation.COMPANY_POC
    if(USER ==Occupation.STUDENT ):
        student_id = session['student_id']
    return render_template('poc_pages/hr_dashboard.html')

@app.route('/poc/my-opportunities')
def poc_opportunities():
    if not ('email' in session ):
        session['url'] = 'index'
        return redirect(url_for('google'))
    USER = session['occupation']
    match USER:
        case 'student':
            USER = Occupation.STUDENT
        case 'poc':
            USER = Occupation.COMPANY_POC
    if(USER ==Occupation.STUDENT ):
        student_id = session['student_id']
    return render_template('poc_pages/opportunity_page.html')

@app.route('/cds/student')
def cds_student():
    if not ('email' in session ):
        session['url'] = 'index'
        return redirect(url_for('google'))
    USER = session['occupation']
    match USER:
        case 'student':
            USER = Occupation.STUDENT
        case 'poc':
            USER = Occupation.COMPANY_POC
    if(USER ==Occupation.STUDENT ):
        student_id = session['student_id']
    return render_template('cds_pages/cds_student_profiles.html')

@app.route('/student')
def student_dashboard():
    if not ('email' in session ):
        session['url'] = 'index'
        return redirect(url_for('google'))
    USER = session['occupation']
    match USER:
        case 'student':
            USER = Occupation.STUDENT
        case 'poc':
            USER = Occupation.COMPANY_POC
    if(USER ==Occupation.STUDENT ):
        student_id = session['student_id']
    return render_template('student_pages/student_dashboard.html')

@app.route('/student/profile')
def student_profile():
    if not ('email' in session ):
        session['url'] = 'index'
        return redirect(url_for('google'))
    USER = session['occupation']
    match USER:
        case 'student':
            USER = Occupation.STUDENT
        case 'poc':
            USER = Occupation.COMPANY_POC
    if(USER ==Occupation.STUDENT ):
        student_id = session['student_id']
    return render_template('student_pages/student_profile.html')

@app.route('/student/resume')
def resume_page():
    if not ('email' in session ):
        session['url'] = 'index'
        return redirect(url_for('google'))
    USER = session['occupation']
    match USER:
        case 'student':
            USER = Occupation.STUDENT
        case 'poc':
            USER = Occupation.COMPANY_POC
    if(USER ==Occupation.STUDENT ):
        student_id = session['student_id']
    return render_template('student_pages/resume_page.html')

@app.route('/student/opportunities/all')
def eligible_page():
    if not ('email' in session ):
        session['url'] = 'index'
        return redirect(url_for('google'))
    USER = session['occupation']
    match USER:
        case 'student':
            USER = Occupation.STUDENT
        case 'poc':
            USER = Occupation.COMPANY_POC
    if(USER ==Occupation.STUDENT ):
        student_id = session['student_id']
    return render_template('student_pages/all.html')

if __name__ == '__main__':
    app.run('localhost',5000,debug=True)

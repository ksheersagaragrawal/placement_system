# pylint: disable=all

from flask import Flask, render_template, request, redirect, jsonify
# from flask.ext.jsonpify import jsonify
from flask_mysqldb import MySQL
import yaml
from enum import Enum
import json
 
class Occupation(Enum):
    STUDENT = 1
    CDS_EMPLOYEE = 2
    COMPANY_POC = 3

USER = Occupation.COMPANY_POC

app = Flask(__name__)

# Configure db
db = yaml.safe_load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

mysql = MySQL(app)

@app.route('/', methods=['GET', 'POST'])
def index():
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
@app.route('/opportunities')
def get_opportunities():
    # we need to check if the user is a student or not
    if(USER != Occupation.STUDENT):
        return jsonify({"error": "Invalid Access"}), 404
    
    # get the student id and status from the request, request will be like: /opportunities?student_id=1&status=applied 
    student_id = request.args.get('student_id')
    status = request.args.get('status')

    # if both student_id and status are not present, return all opportunities with their requirements
    # TO DO: add check for active opportunities
    if student_id is None and status is None:
        cur = mysql.connection.cursor()

        # we execute the query
        resultValue = cur.execute("SELECT * FROM opportunity INNER JOIN requirements ON opportunity.opp_id = requirements.opp_id;")
        
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
    elif student_id is not None and status is not None:
        # similar process as in the above if block is followed based on the conditions specified in the query
        cur = mysql.connection.cursor()
        if status == 'applied':
            query = "select * from selection_procedure where opp_id in (select opp_id from app_opp where student_id = %s)"
            resultValue = cur.execute(query, (student_id,))
            field_names = [i[0] for i in cur.description]
            if resultValue>0:
                opportunities = cur.fetchall()
                final_opportunities = []
                for j in range(len(opportunities)):
                    dict = {}
                    for i in range(len(cur.description)):
                        dict[field_names[i]] = opportunities[j][i]
                    final_opportunities.append(dict)
                return jsonify(final_opportunities)
        elif status == 'rejected' or status == 'eligible' or status == 'not_eligible' or status == 'accepted':
            query = "select * from opportunity where opp_id in (select opp_id from app_opp where student_id = %s)"
            resultValue = cur.execute(query, (student_id,))
            field_names = [i[0] for i in cur.description]
            if resultValue>0:
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
    return jsonify("No matches were found for your search criteria")


@app.route('/opportunity')
def get_opportunity_by_id():
    if(USER != Occupation.STUDENT and USER != Occupation.CDS_EMPLOYEE and USER != Occupation.COMPANY_POC):
        return jsonify({"error": "Invalid Accesss"}), 404
    opp_id = request.args.get('opp_id')
    cur = mysql.connection.cursor()
    resultValue = cur.execute("select * from opportunity where opp_id = %s", (opp_id,))
    field_names = [i[0] for i in cur.description]
    if resultValue > 0:
        opportunity_desc = cur.fetchone()
        dict = {}
        for i in range(len(cur.description)):
            dict[field_names[i]] = opportunity_desc[i]
        return jsonify(dict)
    return jsonify("No matches were found for your search criteria")
    
@app.route('/student')
def get_student_by_id():
    if(USER != Occupation.STUDENT):
        return jsonify({"error": "Invalid Access"}), 404
    stud_id = request.args.get('student_id')
    cur = mysql.connection.cursor()
    resultValue = cur.execute("select * from student where student_id = %s", (stud_id,))
    field_names = [i[0] for i in cur.description]
    if resultValue > 0:
        student_desc = cur.fetchone()
        dict = {}
        for i in range(len(cur.description)):
            dict[field_names[i]] = student_desc[i]
        return jsonify(dict) 
    return jsonify("No matches were found for your search criteria")

@app.route('/poc/opportunity')
def get_opportunity_by_id_for_poc():
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


@app.route('/poc/opportunity/student')
def get_opportunity_by_id_and_round_no_for_poc():
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


@app.route('/opportunity/selected')
def get_student_details_by_opportunity_id():
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


if __name__ == '__main__':
    app.run(debug=True)
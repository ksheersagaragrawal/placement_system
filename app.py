from flask import Flask, render_template, request, redirect
from flask_mysqldb import MySQL
import yaml

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


@app.route('/viewallschema')
def viewallschema():
    cur = mysql.connection.cursor()
    resultValue = cur.execute("show schemas")
    if resultValue > 0:
        userDetails = cur.fetchall()
        return render_template('viewallschema.html',userDetails=userDetails)
    
@app.route('/tables')
def tables():
    cur = mysql.connection.cursor()
    cur.execute("use project;")
    resultValue = cur.execute("show tables")
    if resultValue > 0:
        userDetails = cur.fetchall()
        print(userDetails)
        return render_template('tables.html',userDetails=userDetails)

@app.route('/opportunity')
def viewtableopportunity():
    cur = mysql.connection.cursor()
    resultValue = cur.execute("select * from opportunity")
    if resultValue > 0:
        userDetails = cur.fetchall()
        print(userDetails)
        return render_template('opportunity.html',userDetails=userDetails)
    
@app.route('/app_opp')
def viewtableapp_opp():
    cur = mysql.connection.cursor()
    resultValue = cur.execute("select * from app_opp")
    if resultValue > 0:
        userDetails = cur.fetchall()
        print(userDetails)
        return render_template('app_opp.html',userDetails=userDetails)
@app.route('/application')
def viewtableapplication():
    cur = mysql.connection.cursor()
    resultValue = cur.execute("select * from application")
    if resultValue > 0:
        userDetails = cur.fetchall()
        print(userDetails)
        return render_template('application.html',userDetails=userDetails)
@app.route('/company')
def viewtablecompany():
    cur = mysql.connection.cursor()
    resultValue = cur.execute("select * from company")
    if resultValue > 0:
        userDetails = cur.fetchall()
        print(userDetails)
        return render_template('company.html',userDetails=userDetails)

@app.route('/internship')
def viewtableinternship():
    cur = mysql.connection.cursor()
    resultValue = cur.execute("select * from internship")
    if resultValue > 0:
        userDetails = cur.fetchall()
        print(userDetails)
        return render_template('internship.html',userDetails=userDetails)
@app.route('/placement')
def viewtableplacement():
    cur = mysql.connection.cursor()
    resultValue = cur.execute("select * from placement")
    if resultValue > 0:
        userDetails = cur.fetchall()
        print(userDetails)
        return render_template('placement.html',userDetails=userDetails)
@app.route('/point_of_contact')
def viewtablepointofcontact():
    cur = mysql.connection.cursor()
    resultValue = cur.execute("select * from point_of_contact")
    if resultValue > 0:
        userDetails = cur.fetchall()
        print(userDetails)
        return render_template('point_of_contact.html',userDetails=userDetails)
@app.route('/requirements')
def viewtablerequirements():
    cur = mysql.connection.cursor()
    resultValue = cur.execute("select * from requirements")
    if resultValue > 0:
        userDetails = cur.fetchall()
        print(userDetails)
        return render_template('requirements.html',userDetails=userDetails)

@app.route('/selection_procedure')
def viewtableselectionprocedure():
    cur = mysql.connection.cursor()
    resultValue = cur.execute("select * from selection_procedure")
    if resultValue > 0:
        userDetails = cur.fetchall()
        print(userDetails)
        return render_template('selection_procedure.html',userDetails=userDetails) 
@app.route('/resume')
def viewtableresume():
    cur = mysql.connection.cursor()
    resultValue = cur.execute("select * from resume")
    if resultValue > 0:
        userDetails = cur.fetchall()
        print(userDetails)
        return render_template('resume.html',userDetails=userDetails)  
@app.route('/student')
def viewtablestudent():
     cur = mysql.connection.cursor()
     resultValue = cur.execute("SELECT * FROM student")
     if resultValue > 0:
         userDetails = cur.fetchall()
         return render_template('student.html',userDetails=userDetails)     
    
    
    
    

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, jsonify, flash, session, g, redirect, url_for, json
from app.database.connectDB import DatabaseConnectivity
from app.users.users_model import Users
from app.customers.customers_model import Customers
from app.engineers.engineers_models import Engineers
from app.workorders.work_orders_model import WorkOrders
from app.tickets.tickets_model import Tickets
from passlib.hash import sha256_crypt
import datetime

from datetime import timedelta
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)
import os
import csv
import atexit
from apscheduler.scheduler import Scheduler
from flask_mail import Mail, Message
from flask_cors import CORS, cross_origin
from app.equipments.equipments_model import Equipments
from werkzeug import secure_filename
dbInstance = DatabaseConnectivity()
usersInstance = Users()
custInstance = Customers()
engineersInstance = Engineers()
ordersInstance = WorkOrders()
ticketInstance = Tickets()
equipmentInstance = Equipments()

app = Flask(__name__)
app.secret_key = 'mysecretkeyghjngdssdfghjhdfhghhsffdtrdddvdvbggdsewwessaae'

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

app.config['JWT_SECRET_KEY'] = 'somesecretstuffsforjwt'
jwt = JWTManager(app)

app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=1)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'zubacxnotification@gmail.com'
app.config['MAIL_PASSWORD'] = 'zubacx123!'

mail = Mail(app)

app.config['UPLOAD_FOLDER'] = '/Users/walternyeko/Desktop/Tests/uploads/'

@app.before_request
def before_request():
    g.username = None
    if 'username' in session:
        g.username = session['username']


@app.route('/login')
def index():
    session.pop('username', None)
    return render_template('index.html')


@app.route('/index', methods=['GET', 'POST'])
def login():
    session.pop('username', None)
    username = request.form['username']
    password_candidate = request.form['password']

    conn = dbInstance.connectToDatabase()
    cur = conn.cursor()
    cur.execute(
        "SELECT user_name,user_password from users WHERE user_name=%s", [username])

    data = cur.fetchone()
    if not data:
        flash('Invalid Credentials', 'danger')
        return render_template('index.html')
    usernameDB = data[0]
    if usernameDB == username:
        password = data[1]
        if sha256_crypt.verify(password_candidate, password):
            session['username'] = username
            LoggedInUser1 = usersInstance.checkUserRights(username)
            allTheTickets = ticketInstance.view_all_tickets()
            myTickets = ticketInstance.view_all_my_tickets(username)
            number_of_atm_open = ticketInstance.number_of_open_atm()
            number_of_air_open = ticketInstance.number_of_open_air()
            number_of_tel_open = ticketInstance.number_of_open_tel()
            number_of_fle_open = ticketInstance.number_of_open_fle()
            return render_template('dashboard.html',
            allTheTickets=allTheTickets,
            currentUser=LoggedInUser1,
            allMyTickets=myTickets,
            number_of_atm_open=number_of_atm_open,
            number_of_air_open=number_of_air_open,
            number_of_tel_open=number_of_tel_open,
            number_of_fle_open=number_of_fle_open)

        else:
            
            flash('Invalid Credentials', 'danger')
            return render_template('index.html')
    else:
        flash('{} is not registered'.format(username), 'danger')
        return render_template('index.html')

@app.route('/new_ticket')
def new_ticket():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    theClients = ticketInstance.get_clients()
    theEngineers = ticketInstance.get_engineers()
    theWorkOrderTypes = ticketInstance.get_work_order_types()
    if g.username:
        return render_template('new_ticket.html',theWorkOrderTypes=theWorkOrderTypes, theEngineers=theEngineers, theClients=theClients,currentUser=LoggedInUser1)
    return render_template('index.html')
    
@app.route('/add_ticket', methods=['POST'])
def add_ticket():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    ticket_assigned_to = request.form['ticket_assigned_to']
    ticket_status =  request.form['ticket_status']
    hours_to_add = request.form['hours_to_add']
    ticket_opening_time = datetime.datetime.now()
    ticket_overdue_time =  datetime.datetime.now() + timedelta(hours=int(hours_to_add))
    ticket_client =  request.form['ticket_client']
    ticket_po_number = request.form['ticket_po_number']
    ticket_wo_type = request.form['ticket_wo_type']
    ticket_reason = request.form['ticket_reason']
    ticket_planned_visit_date = request.form['ticket_planned_visit_date']
    ticket_actual_visit_date = request.form['ticket_actual_visit_date']
    ticket_priority = request.form['ticket_priority']
    ticket_site_id = request.form['ticket_site_id']

    ticket_type_ATM = request.form.get('ATM')
    if ticket_type_ATM:
        ticket_type_value = 1
    else:
        ticket_type_value = 0

    ticket_type_Airport = request.form.get('airport')
    if ticket_type_Airport:
        ticket_type_value = 2
    else:
        ticket_type_value = ticket_type_value

    ticket_type_telecom = request.form.get('telecom')
    if ticket_type_telecom:
        ticket_type_value = 3
    else:
        ticket_type_value = ticket_type_value

    ticket_type_fleet = request.form.get('fleet')
    if ticket_type_fleet:
        ticket_type_value = 4
    else:
        ticket_type_value = ticket_type_value

    ticket_revisited = request.form.get('revisit')
    if ticket_revisited:
        ticket_revisited_value = "Yes"
    else:
        ticket_revisited_value = "No"

    username = session['username']

    ticketInstance.add_ticket(ticket_assigned_to,ticket_opening_time,
    ticket_status,ticket_overdue_time,ticket_planned_visit_date,ticket_actual_visit_date,
    ticket_client,ticket_po_number,ticket_wo_type,ticket_reason,
    ticket_priority,username,ticket_type_value,ticket_revisited_value, ticket_site_id)
    theClients = ticketInstance.get_clients()
    theEngineers = ticketInstance.get_engineers()
    theWorkOrderTypes = ticketInstance.get_work_order_types()
    users = usersInstance.users_who_can_receive_email(ticket_client)
    recipients = []
    for email in users[0]:
        recipients = email.split(',')
    message="""A ticket has just been opened and assigend to engineer {}, 
the reason for this ticket is to address the issue of {}. You are receiving this notification because 
your account with Zubacx call-center system is configured to receive these alerts.""".format(ticket_assigned_to,ticket_reason)
    send_email_alerts('Ticket Opened',recipients,body=message)
    if g.username:
        return render_template('new_ticket.html',theWorkOrderTypes=theWorkOrderTypes, theEngineers=theEngineers, theClients=theClients,currentUser=LoggedInUser1)
    return render_template('index.html')

@app.route('/edit_the_ticket/<int:ticket_id>', methods=['GET'])
def get_ticket_details_for_edit(ticket_id):
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    theReturnedTicket = ticketInstance.get_ticket_by_Id(ticket_id)
    if g.username:
        return render_template('edit_ticket.html', allTheTickets=theReturnedTicket,currentUser=LoggedInUser1)
    return render_template('index.html')


@app.route('/edit_ticket/<int:ticket_id>', methods=['POST'])
def edit_ticket(ticket_id):
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    ticket_assigned_to = request.form['ticket_assigned_to_edit']
    ticket_status =  request.form['ticket_status_edit']
    hours_to_add = request.form['hours_to_add_edit']
    current_ticket_overdue_time = ticketInstance.get_ticket_overdue_time_by_Id(ticket_id)
    ticket_overdue_time =  current_ticket_overdue_time[0] + timedelta(hours=int(hours_to_add))
    ticket_client =  request.form['ticket_client_edit']
    ticket_po_number = request.form['ticket_po_number_edit']
    ticket_wo_type = request.form['ticket_wo_type_edit']
    ticket_reason = request.form['ticket_reason_edit']
    ticket_client_visit_note = "Just for test...no client visited site"
    ticket_planned_visit_date = request.form['ticket_planned_visit_date_edit']
    ticket_actual_visit_date = request.form['ticket_actual_visit_date_edit']
    ticket_priority = request.form['ticket_priority_edit']
    ticket_root_cause = request.form['ticket_root_cause_edit']
    ticket_action_taken = request.form['ticket_action_taken_edit']
    ticket_pending_reason = request.form['ticket_pending_reason_edit']
    ticket_additional_note = request.form['ticket_additional_note_edit']
    ticket_dispatch_time = request.form['ticket_dispatch_time']
    ticket_arrival_time = request.form['ticket_arrival_time']
    ticket_start_time = request.form['ticket_start_time']
    ticket_complete_time = request.form['ticket_complete_time']
    ticket_return_time = request.form['ticket_return_time']
    ticket_site_id = request.form['ticket_site_id_edit']
    if ticket_status == "Closed":
        ticket_closing_time = datetime.datetime.now()
    else:
        ticket_closing_time = None

    ticket_type_ATM = request.form.get('ATM_edit')
    if ticket_type_ATM:
        ticket_type_value = 1
    else:
        ticket_type_value = 0

    ticket_type_Airport = request.form.get('airport_edit')
    if ticket_type_Airport:
        ticket_type_value = 2
    else:
        ticket_type_value = ticket_type_value

    ticket_type_telecom = request.form.get('telecom_edit')
    if ticket_type_telecom:
        ticket_type_value = 3
    else:
        ticket_type_value = ticket_type_value

    ticket_type_fleet = request.form.get('fleet_edit')
    if ticket_type_fleet:
        ticket_type_value = 4
    else:
        ticket_type_value = ticket_type_value

    ticketInstance.edit_ticket(ticket_assigned_to,
    ticket_status,ticket_overdue_time,ticket_planned_visit_date,ticket_actual_visit_date,
    ticket_client,ticket_po_number,ticket_wo_type,ticket_reason,ticket_client_visit_note,
    ticket_priority,ticket_root_cause,
    ticket_action_taken,ticket_pending_reason,ticket_additional_note,ticket_site_id,ticket_closing_time,
    ticket_dispatch_time,ticket_arrival_time,ticket_start_time,ticket_complete_time,
    ticket_return_time,ticket_type_value,ticket_id)
    if ticket_status == "Closed":
        users = usersInstance.users_who_can_receive_email(ticket_client)
        recipients = []
        for email in users[0]:
            recipients = email.split(',')
        message="""The ticket regarding the issue of {} has just been closed by engineer {}. You are receiving this notification because 
your account with Zubacx call-center system is configured to receive these alerts.""".format(ticket_reason,ticket_assigned_to)
        send_email_alerts('Ticket Closed',recipients,body=message)
    theClients = ticketInstance.get_clients()
    theEngineers = ticketInstance.get_engineers()
    theWorkOrderTypes = ticketInstance.get_work_order_types()
    return render_template('new_ticket.html',theWorkOrderTypes=theWorkOrderTypes, theEngineers=theEngineers, theClients=theClients,currentUser=LoggedInUser1)


@app.route('/view_all_tickets', methods=['GET'])
def view_all_tickets():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    allTheTickets = ticketInstance.view_all_tickets()
    myTickets = ticketInstance.view_all_my_tickets(LoggedInUser)
    if g.username:
        return render_template('all_tickets.html', 
        allTheTickets=allTheTickets, 
        currentUser=LoggedInUser1,
        myTickets=myTickets)
    return redirect(url_for('index'))

@app.route('/delete_tickets/<int:ticket_id>', methods=['DELETE','POST'])
def delete_ticket(ticket_id):
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    ticketInstance.delete_a_ticket(ticket_id)
    allTheTickets = ticketInstance.view_all_tickets()
    myTickets = ticketInstance.view_all_my_tickets(LoggedInUser)
    if g.username:
        return render_template('all_tickets.html', 
        allTheTickets=allTheTickets, 
        currentUser=LoggedInUser1,
        myTickets=myTickets
        )
    return redirect(url_for('index'))
    

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    allTheTickets = ticketInstance.view_all_tickets()
    myTickets = ticketInstance.view_all_my_tickets(LoggedInUser)
    number_of_atm_open = ticketInstance.number_of_open_atm()
    number_of_air_open = ticketInstance.number_of_open_air()
    number_of_tel_open = ticketInstance.number_of_open_tel()
    number_of_fle_open = ticketInstance.number_of_open_fle()
    if g.username:
        return render_template('dashboard.html', 
        allTheTickets=allTheTickets, 
        currentUser=LoggedInUser1,
        myTickets=myTickets, 
        number_of_atm_open=number_of_atm_open,
        number_of_air_open=number_of_air_open,
        number_of_tel_open=number_of_tel_open,
        number_of_fle_open=number_of_fle_open
        )
    return redirect(url_for('index'))

@app.route('/reports')
def reports():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    allTheTickets = ticketInstance.get_tickets_for_reports()
    if g.username:
        return render_template('reports.html', currentUser=LoggedInUser1,allTheTickets=allTheTickets)
    return redirect(url_for('index'))

@app.route('/tasks')
def tasks():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)

    ATM_running = ticketInstance.get_ATM_running_tasks()
    Airport_running = ticketInstance.get_Airport_running_tasks()
    Telecom_running = ticketInstance.get_Telecom_running_tasks()
    Fleet_running = ticketInstance.get_Fleet_running_tasks()

    ATM_due_soon = ticketInstance.get_ATM_due_soon_tasks()
    Airport_due_soon = ticketInstance.get_Airport_due_soon_tasks()
    Telecom_due_soon = ticketInstance.get_Telecom_due_soon_tasks()
    Fleet_due_soon = ticketInstance.get_Fleet_due_soon_tasks()

    ATM_completed = ticketInstance.get_ATM_completed_tasks()
    Airport_completed = ticketInstance.get_Airport_completed_tasks()
    Telecom_completed = ticketInstance.get_Telecom_completed_tasks()
    Fleet_completed = ticketInstance.get_Fleet_completed_tasks()

    ATM_overdue = ticketInstance.get_ATM_overdue_tasks()
    Airport_overdue = ticketInstance.get_Airport_overdue_tasks()
    Telecom_overdue = ticketInstance.get_Telecom_overdue_tasks()
    Fleet_overdue = ticketInstance.get_Fleet_overdue_tasks()


    ATM_running_value = ATM_running[0][0]
    Airport_running_value = Airport_running[0][0]
    Telecom_running_value = Telecom_running[0][0]
    Fleet_running_value = Fleet_running[0][0]

    ATM_overdue_value = ATM_overdue[0][0]
    Airport_overdue_value = Airport_overdue[0][0]
    Telecom_overdue_value = Telecom_overdue[0][0]
    Fleet_overdue_value = Fleet_overdue[0][0]

    ATM_due_soon_value = ATM_due_soon[0][0]
    Airport_due_soon_value = Airport_due_soon[0][0]
    Telecom_due_soon_value = Telecom_due_soon[0][0]
    Fleet_due_soon_value = Fleet_due_soon[0][0]

    ATM_completed_value = ATM_completed[0][0]
    Airport_completed_value = Airport_completed[0][0]
    Telecom_completed_value = Telecom_completed[0][0]
    Fleet_completed_value = Fleet_completed[0][0]
    if g.username:
        return render_template('tasks.html', currentUser=LoggedInUser1, 
        ATM_running_value=ATM_running_value, Airport_running_value=Airport_running_value,
        Telecom_running_value=Telecom_running_value,Fleet_running_value=Fleet_running_value,
        ATM_completed_value=ATM_completed_value,Telecom_completed_value=Telecom_completed_value,
        Airport_completed_value=Airport_completed_value,Fleet_completed_value=Fleet_completed_value,
        ATM_due_soon_value=ATM_due_soon_value,Airport_due_soon_value=Airport_due_soon_value,
        Telecom_due_soon_value=Telecom_due_soon_value,Fleet_due_soon_value=Fleet_due_soon_value,
        ATM_overdue_value=ATM_overdue_value,Airport_overdue_value=Airport_overdue_value,
        Telecom_overdue_value=Telecom_overdue_value,Fleet_overdue_value=Fleet_overdue_value
        )
    return redirect(url_for('index'))

@app.route('/client')
def new_customer():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    if g.username:
        return render_template('new_customer.html', currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/user')
def new_users():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    theClients = custInstance.get_all_clients()
    theReturnedUser = usersInstance.get_no_user()
    if g.username:
        return render_template('new_users.html', allTheUsers=theReturnedUser,currentUser=LoggedInUser1, theClients=theClients)
    return redirect(url_for('index'))
@app.route('/engineer')
def new_engineer():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    if g.username:
        return render_template('new_engineer.html',currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/new_equipment')
def new_equipment():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    if g.username:
        return render_template('new_equipment.html',currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/workorder')
def new_workorder():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    if g.username:
        return render_template('new_workorder.html',currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/add_user', methods=['POST'])
def add_user():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    firstName = request.form['user_first_name']
    lastName = request.form['user_last_name']
    userName = request.form['user_name']
    email = request.form['user_email']
    userAddress = request.form['user_physical_address']
    userPhone = request.form['user_phone']
    userPassword = request.form['user_password']
    user_client = request.form.get('user_client')

    can_add_user = request.form.get('can_add_user')
    if can_add_user:
        can_add_user_value = 1
    else:
        can_add_user_value = 0

    client_account = request.form.get('client_account')
    if client_account:
        client_account_value = 1
    else:
        client_account_value = 0

    can_delete_user = request.form.get('can_delete_user')
    if can_delete_user:
        can_delete_user_value = 1
    else:
        can_delete_user_value = 0

    can_edit_user = request.form.get('can_edit_user')
    if can_edit_user:
        can_edit_user_value = 1
    else:
        can_edit_user_value = 0

    can_edit_his_info = request.form.get('can_edit_his_info')
    if can_edit_his_info:
        can_edit_his_info_value = 1
    else:
        can_edit_his_info_value = 0

    can_open_tickets = request.form.get('can_open_tickets')
    if can_open_tickets:
        can_open_tickets_value = 1
    else:
        can_open_tickets_value = 0

    can_edit_tickets = request.form.get('can_edit_tickets')
    if can_edit_tickets:
        can_edit_tickets_value = 1
    else:
        can_edit_tickets_value = 0

    can_delete_tickets = request.form.get('can_delete_tickets')
    if can_delete_tickets:
        can_delete_tickets_value = 1
    else:
        can_delete_tickets_value = 0

    can_view_all_tickets = request.form.get('can_view_all_tickets')
    if can_view_all_tickets:
        can_view_all_tickets_value = 1
    else:
        can_view_all_tickets_value = 0

    can_view_his_tickets = request.form.get('can_view_his_tickets')
    if can_view_his_tickets:
        can_view_his_tickets_value = 1
    else:
        can_view_his_tickets_value = 0

    can_edit_his_tickets = request.form.get('can_edit_his_tickets')
    if can_edit_his_tickets:
        can_edit_his_tickets_value = 1
    else:
        can_edit_his_tickets_value = 0

    can_view_his_tasks = request.form.get('can_view_his_tasks')
    if can_view_his_tasks:
        can_view_his_tasks_value = 1
    else:
        can_view_his_tasks_value = 0

    can_view_all_tasks = request.form.get('can_view_all_tasks')
    if can_view_all_tasks:
        can_view_all_tasks_value = 1
    else:
        can_view_all_tasks_value = 0

    can_view_his_reports = request.form.get('can_view_his_reports')
    if can_view_his_reports:
        can_view_his_reports_value = 1
    else:
        can_view_his_reports_value = 0

    can_view_all_reports = request.form.get('can_view_all_reports')
    if can_view_all_reports:
        can_view_all_reports_value = 1
    else:
        can_view_all_reports_value = 0

    can_add_delete_edit_client = request.form.get('can_add_delete_edit_clients')
    if can_add_delete_edit_client:
        can_add_delete_edit_client_value = 1
    else:
        can_add_delete_edit_client_value = 0

    can_add_delete_edit_engineer = request.form.get('can_add_delete_edit_engineers')
    if can_add_delete_edit_engineer:
        can_add_delete_edit_engineer_value = 1
    else:
        can_add_delete_edit_engineer_value = 0


    can_add_delete_edit_equipment = request.form.get('can_add_delete_edit_equipment')
    if can_add_delete_edit_equipment:
        can_add_delete_edit_equipment_value = 1
    else:
        can_add_delete_edit_equipment_value = 0


    can_add_delete_edit_workorder = request.form.get('can_add_delete_edit_workorder')
    if can_add_delete_edit_workorder:
        can_add_delete_edit_workorder_value = 1
    else:
        can_add_delete_edit_workorder_value = 0

    user_can_receive_email_alerts = request.form.get('can_receive_email_alerts')
    if user_can_receive_email_alerts:
        user_can_receive_email_alerts_value = 1
    else:
        user_can_receive_email_alerts_value = 0

    encryptedPassword = sha256_crypt.encrypt(str(userPassword))
    usersInstance.add_user(firstName,lastName,email,userAddress,userPhone,userName,encryptedPassword,
    can_add_user_value,can_delete_user_value,can_edit_user_value,can_edit_his_info_value,
    can_open_tickets_value,can_edit_tickets_value,can_delete_tickets_value,can_view_all_tickets_value,
    can_view_his_tickets_value,can_edit_his_tickets_value,can_view_his_tasks_value,can_view_all_tasks_value,
    can_view_his_reports_value,can_view_all_reports_value,can_add_delete_edit_client_value,
    can_add_delete_edit_engineer_value,can_add_delete_edit_equipment_value,can_add_delete_edit_workorder_value,
    user_can_receive_email_alerts_value,client_account_value,user_client)
    theReturnedUsers = usersInstance.view_all_users()
    if g.username:
        return render_template('view_users.html', allTheUsers=theReturnedUsers,currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/add_client', methods=['POST'])
def add_client():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    customer_name = request.form['customer_name']
    customer_email = request.form['customer_email']
    customer_phone = request.form['customer_phone']
    customer_address = request.form['customer_address']
    customer_product = request.form['customer_product']
    customer_contact_person = request.form['customer_contact_person']
    custInstance.add_client(customer_name,customer_phone,customer_email,
    customer_address,customer_product,customer_contact_person)
    if g.username:
        return render_template('new_customer.html',currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/add_engineer', methods=['POST'])
def add_engineer():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    engineer_first_name = request.form['engineer_first_name']
    engineer_last_name = request.form['engineer_last_name']
    engineer_email = request.form['engineer_email']
    engineer_phone = request.form['engineer_phone']
    engineer_address = request.form['engineer_address']
    engineer_field_ATM = request.form.get('engineer_field_ATM')
    if engineer_field_ATM:
        engineer_field_ATM_Value = 1
    else:
        engineer_field_ATM_Value = 0

    engineer_field_AIR = request.form.get('engineer_field_AIR')
    if engineer_field_AIR:
        engineer_field_AIR_Value = 1
    else:
        engineer_field_AIR_Value = 0

    engineer_field_TEL = request.form.get('engineer_field_TEL')
    if engineer_field_TEL:
        engineer_field_TEL_Value = 1
    else:
        engineer_field_TEL_Value = 0

    engineersInstance.add_engineer(engineer_first_name,engineer_last_name,engineer_phone,engineer_email,engineer_address,engineer_field_ATM_Value,engineer_field_AIR_Value,engineer_field_TEL_Value)
    if g.username:
        return render_template('new_engineer.html',currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/all_users', methods=['GET'])
def all_users():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    theReturnedUsers = usersInstance.view_all_users()
    if g.username:
        return render_template('view_users.html', allTheUsers=theReturnedUsers,currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/all_admin_users', methods=['GET'])
def all_admin_users():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    theReturnedUsers = usersInstance.view_all_admin_users()
    if g.username:
        return render_template('view_users.html', allTheUsers=theReturnedUsers,currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/all_ordinary_users', methods=['GET'])
def all_ordinary_users():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    theReturnedUsers = usersInstance.view_all_ordinary_users()
    if g.username:
        return render_template('view_users.html', allTheUsers=theReturnedUsers,currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/all_the_users/<int:user_id>', methods=['DELETE','POST'])
def delete_user(user_id):
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    usersInstance.delete_a_user(user_id)
    theReturnedUsers = usersInstance.view_all_users()
    if g.username:
        return render_template('view_users.html', allTheUsers=theReturnedUsers,currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/the_user/<int:user_id>', methods=['GET'])
def get_user_by_Id(user_id):
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    theReturnedUser = usersInstance.get_user_by_Id(user_id)
    if g.username:
        return render_template('new_users.html', allTheUsers=theReturnedUser,currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/edit_the_user/<int:user_id>', methods=['GET'])
def get_user_details_for_edit(user_id):
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    theReturnedUser = usersInstance.get_user_by_Id(user_id)
    theClients = ticketInstance.get_clients()
    if g.username:
        return render_template('edit_user.html', allTheUsers=theReturnedUser,
        currentUser=LoggedInUser1,theClients=theClients)
    return redirect(url_for('index'))

@app.route('/edit_user/<int:user_id>', methods=['POST'])
def edit_user(user_id):
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    firstName = request.form['user_first_name_edit']
    lastName = request.form['user_last_name_edit']
    userName = request.form['user_name_edit']
    email = request.form['user_email_edit']
    userAddress = request.form['user_address_edit']
    userPhone = request.form['user_phone_edit']
    userPassword = request.form['user_password_edit']
    userClient = request.form.get('user_client_edit')

    user_role = request.form.get('client_account_edit')
    if user_role:
        user_role_value = 1
    else:
        user_role_value = 0

    can_add_user = request.form.get('can_add_user_edit')
    if can_add_user:
        can_add_user_value = 1
    else:
        can_add_user_value = 0

    can_delete_user = request.form.get('can_delete_user_edit')
    if can_delete_user:
        can_delete_user_value = 1
    else:
        can_delete_user_value = 0

    can_edit_user = request.form.get('can_edit_user_edit')
    if can_edit_user:
        can_edit_user_value = 1
    else:
        can_edit_user_value = 0

    can_edit_his_info = request.form.get('can_edit_his_info_edit')
    if can_edit_his_info:
        can_edit_his_info_value = 1
    else:
        can_edit_his_info_value = 0

    can_open_tickets = request.form.get('can_open_tickets_edit')
    if can_open_tickets:
        can_open_tickets_value = 1
    else:
        can_open_tickets_value = 0

    can_edit_tickets = request.form.get('can_edit_tickets_edit')
    if can_edit_tickets:
        can_edit_tickets_value = 1
    else:
        can_edit_tickets_value = 0

    can_delete_tickets = request.form.get('can_delete_tickets_edit')
    if can_delete_tickets:
        can_delete_tickets_value = 1
    else:
        can_delete_tickets_value = 0

    can_view_all_tickets = request.form.get('can_view_all_tickets_edit')
    if can_view_all_tickets:
        can_view_all_tickets_value = 1
    else:
        can_view_all_tickets_value = 0

    can_view_his_tickets = request.form.get('can_view_his_tickets_edit')
    if can_view_his_tickets:
        can_view_his_tickets_value = 1
    else:
        can_view_his_tickets_value = 0

    can_edit_his_tickets = request.form.get('can_edit_his_tickets_edit')
    if can_edit_his_tickets:
        can_edit_his_tickets_value = 1
    else:
        can_edit_his_tickets_value = 0

    can_view_his_tasks = request.form.get('can_view_his_tasks_edit')
    if can_view_his_tasks:
        can_view_his_tasks_value = 1
    else:
        can_view_his_tasks_value = 0

    can_view_all_tasks = request.form.get('can_view_all_tasks_edit')
    if can_view_all_tasks:
        can_view_all_tasks_value = 1
    else:
        can_view_all_tasks_value = 0

    can_view_his_reports = request.form.get('can_view_his_reports_edit')
    if can_view_his_reports:
        can_view_his_reports_value = 1
    else:
        can_view_his_reports_value = 0

    can_view_all_reports = request.form.get('can_view_all_reports_edit')
    if can_view_all_reports:
        can_view_all_reports_value = 1
    else:
        can_view_all_reports_value = 0

    can_add_delete_edit_client = request.form.get('can_add_delete_edit_clients_edit')
    if can_add_delete_edit_client:
        can_add_delete_edit_client_value = 1
    else:
        can_add_delete_edit_client_value = 0

    can_add_delete_edit_engineer = request.form.get('can_add_delete_edit_engineers_edit')
    if can_add_delete_edit_engineer:
        can_add_delete_edit_engineer_value = 1
    else:
        can_add_delete_edit_engineer_value = 0


    can_add_delete_edit_equipment = request.form.get('can_add_delete_edit_equipment_edit')
    if can_add_delete_edit_equipment:
        can_add_delete_edit_equipment_value = 1
    else:
        can_add_delete_edit_equipment_value = 0


    can_add_delete_edit_workorder = request.form.get('can_add_delete_edit_workorder_edit')
    if can_add_delete_edit_workorder:
        can_add_delete_edit_workorder_value = 1
    else:
        can_add_delete_edit_workorder_value = 0

    user_can_receive_email_alerts = request.form.get('can_receive_email_alerts_edit')
    if user_can_receive_email_alerts:
        user_can_receive_email_alerts_value = 1
    else:
        user_can_receive_email_alerts_value = 0

    encryptedPassword = sha256_crypt.encrypt(str(userPassword))
    usersInstance.edit_a_user(user_id,firstName, lastName,email,userPhone,userAddress,userName,encryptedPassword,
    can_add_user_value,can_delete_user_value,can_edit_user_value,can_edit_his_info_value,
    can_open_tickets_value,can_edit_tickets_value,can_delete_tickets_value,can_view_all_tickets_value,
    can_view_his_tickets_value,can_edit_his_tickets_value,can_view_his_tasks_value,can_view_all_tasks_value,
    can_view_his_reports_value,can_view_all_reports_value,can_add_delete_edit_client_value,
    can_add_delete_edit_engineer_value,can_add_delete_edit_equipment_value,can_add_delete_edit_workorder_value,
    user_can_receive_email_alerts_value,user_role_value, userClient)
    theReturnedUsers = usersInstance.view_all_users()
    if g.username:
        return render_template('view_users.html', allTheUsers=theReturnedUsers,currentUser=LoggedInUser1)
    return redirect(url_for('index'))

# WORK ORDERS

@app.route('/edit_the_work_order/<int:work_order_id>', methods=['GET'])
def edit_the_work_order(work_order_id):
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    theReturnedOrder = ordersInstance.get_work_order_by_Id(work_order_id)
    if g.username:
        return render_template('edit_work_order.html', allTheOrders=theReturnedOrder,currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/add_work_order', methods=['POST'])
def add_work_order():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    work_order_type = request.form['work_order_type']
    ordersInstance.add_work_order(work_order_type)
    theReturnedOrders = ordersInstance.view_all_work_orders()
    if g.username:
        return render_template('new_workorder.html', allTheOrders=theReturnedOrders,currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/edit_the_work_order/<int:work_order_id>', methods=['POST'])
def edit_work_order(work_order_id):
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    workOrderType = request.form['work_order_type_edit']
    ordersInstance.edit_a_work_order(work_order_id,workOrderType)
    theReturnedOrders = ordersInstance.view_all_work_orders()
    if g.username:
        return render_template('view_work_order.html', allTheOrders=theReturnedOrders,currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/all_the_work_orders/<int:work_order_id>', methods=['POST','DELETE'])
def delete_work_order(work_order_id):
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    ordersInstance.delete_a_work_order(work_order_id)
    theReturnedOrders = ordersInstance.view_all_work_orders()
    if g.username:
        return render_template('view_work_order.html', allTheOrders=theReturnedOrders,currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/all_work_orders', methods=['GET'])
def all_work_orders():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    theReturnedOrders = ordersInstance.view_all_work_orders()
    if g.username:
        return render_template('view_work_order.html', allTheOrders=theReturnedOrders,currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/all_work_orders_completed', methods=['GET'])
def all_work_orders_completed():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    theReturnedOrders = ordersInstance.view_all_work_orders()
    if g.username:
        return render_template('view_work_order.html', allTheOrders=theReturnedOrders,currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET'])
def user_profile():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    if g.username:
        return render_template('profile.html',currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/all_work_orders_pending', methods=['GET'])
def all_work_orders_pending():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    theReturnedOrders = ordersInstance.view_all_work_orders()
    if g.username:
        return render_template('view_work_order.html', allTheOrders=theReturnedOrders,currentUser=LoggedInUser1)
    return redirect(url_for('index'))

# OUR EQUIPMENTS

@app.route('/all_equipments', methods=['GET'])
def all_equipments():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    theReturnedEquipments = equipmentInstance.get_all_equipments()
    if g.username:
        return render_template('our_equipments.html', allTheEquipments=theReturnedEquipments,currentUser=LoggedInUser1)
    return redirect(url_for('index'))

# OUR CLIENTS

@app.route('/all_clients', methods=['GET'])
def all_clients():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    theReturnedClients = custInstance.get_all_clients()
    if g.username:
        return render_template('our_clients.html', allTheClients=theReturnedClients,currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/all_the_clients/<int:client_id>', methods=['POST','DELETE'])
def delete_client(client_id):
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    custInstance.delete_a_client(client_id)
    theReturnedClients = custInstance.get_all_clients()
    if g.username:
        return render_template('view_clients.html', allTheClients=theReturnedClients,currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/the_client/<int:client_id>', methods=['GET'])
def get_client_by_Id(client_id):
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    theReturnedClient = custInstance.get_client_by_Id(client_id)
    if g.username:
        return render_template('new_customer.html', allTheClients=theReturnedClient,currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/edit_the_client/<int:client_id>', methods=['GET'])
def get_client_details_for_edit(client_id):
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    theReturnedClient = custInstance.get_client_by_Id(client_id)
    if g.username:
        return render_template('edit_customer.html', allTheClients=theReturnedClient,currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/edit_client/<int:client_id>', methods=['POST'])
def edit_client(client_id):
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    clientName = request.form['customer_name_edit']
    clientProduct = request.form['customer_product_edit']
    clientAddress = request.form['customer_address_edit']
    clientPhone = request.form['customer_phone_edit']
    clientEmail = request.form['customer_email_edit']
    customer_contact_person = request.form['customer_contact_person_edit']
   
    custInstance.edit_a_client(client_id,clientName, clientProduct,clientAddress,clientPhone,clientEmail,customer_contact_person)
    theReturnedClients = custInstance.get_all_clients()
    if g.username:
        return render_template('our_clients.html', allTheClients=theReturnedClients,currentUser=LoggedInUser1)
    return redirect(url_for('index'))
# OUR ENGINEERS

@app.route('/all_engineers', methods=['GET'])
def all_engineers():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    theReturnedEngineers = engineersInstance.get_all_engineers()
    if g.username:
        return render_template('view_engineers.html', allTheEngineers=theReturnedEngineers,currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/all_the_engineers/<int:engineer_id>', methods=['POST','DELETE'])
def delete_engineer(engineer_id):
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    engineersInstance.delete_a_engineer(engineer_id)
    theReturnedEngineers = engineersInstance.get_all_engineers()
    if g.username:
        return render_template('view_engineers.html', allTheEngineers=theReturnedEngineers,currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/the_engineer/<int:engineer_id>', methods=['GET'])
def get_engineer_by_Id(engineer_id):
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    theReturnedEngineer = engineersInstance.get_engineer_by_Id(engineer_id)
    if g.username:
        return render_template('new_engineer.html', allTheEngineers=theReturnedEngineer,currentUser=LoggedInUser1)
    return redirect(url_for('index'))
    
@app.route('/edit_the_engineer/<int:engineer_id>', methods=['GET'])
def get_engineer_details_for_edit(engineer_id):
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    theReturnedEngineer = engineersInstance.get_engineer_by_Id(engineer_id)
    if g.username:
        return render_template('edit_engineer.html', allTheEngineers=theReturnedEngineer,currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/edit_engineer/<int:engineer_id>', methods=['POST'])
def edit_engineer(engineer_id):
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    engineer_first_name = request.form['engineer_first_name_edit']
    engineer_last_name = request.form['engineer_last_name_edit']
    engineer_email = request.form['engineer_email_edit']
    engineer_phone = request.form['engineer_phone_edit']
    engineer_address = request.form['engineer_address_edit']
    engineer_field_ATM = request.form.get('engineer_field_ATM_edit')
    if engineer_field_ATM:
        engineer_field_ATM_Value = 1
    else:
        engineer_field_ATM_Value = 0

    engineer_field_AIR = request.form.get('engineer_field_AIR_edit')
    if engineer_field_AIR:
        engineer_field_AIR_Value = 1
    else:
        engineer_field_AIR_Value = 0

    engineer_field_TEL = request.form.get('engineer_field_TEL_edit')
    if engineer_field_TEL:
        engineer_field_TEL_Value = 1
    else:
        engineer_field_TEL_Value = 0

    engineersInstance.edit_an_engineer(engineer_id,engineer_first_name,engineer_last_name,engineer_address,engineer_phone,engineer_email,engineer_field_ATM_Value,engineer_field_AIR_Value,engineer_field_TEL_Value)
    theReturnedEngineers = engineersInstance.get_all_engineers()
    if g.username:
        return render_template('view_engineers.html', allTheEngineers=theReturnedEngineers,currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/robot', methods=['GET'])
def user_is_missing_permission():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    if g.username:
        return render_template('rights_messages.html',currentUser=LoggedInUser1)
    return redirect(url_for('index'))

# @app.route('/tasks', methods=['GET'])
# @cross_origin
# def get_tasks():
#     data = [{'value':12},{'value1':12},{'value2':23}]
#     return jsonify({'Data':data})

@app.route('/open_and_overdue_tickets')
def open_and_overdue_tickets():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    allTheTickets = ticketInstance.view_all_open_tickets()
    if g.username:
        return render_template('open_tickets.html', 
        currentUser=LoggedInUser1, allTheTickets=allTheTickets)
    else:
        return render_template('index.html')


@app.route('/closed_and_overdue_tickets')
def closed_and_overdue_tickets():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    allTheTickets = ticketInstance.view_all_closed_tickets()
    if g.username:
        return render_template('closed_tickets.html', 
        currentUser=LoggedInUser1, allTheTickets=allTheTickets)
    else:
        return render_template('index.html')


@app.route('/low_priority_and_overdue_tickets')
def low_priority_and_overdue_tickets():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    allTheTickets = ticketInstance.view_all_overdue_tickets()
    if g.username:
        return render_template('overdue_tickets.html', 
        currentUser=LoggedInUser1, allTheTickets=allTheTickets)
    else:
        return render_template('index.html')


@app.route('/my_open_and_overdue_tickets')
def my_open_and_overdue_tickets():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    allTheTickets = ticketInstance.view_all_my_open_tickets(LoggedInUser)
    if g.username:
        return render_template('my_open_tickets.html', 
        currentUser=LoggedInUser1, allTheTickets=allTheTickets)
    else:
        return render_template('index.html')


@app.route('/my_closed_and_overdue_tickets')
def my_closed_and_overdue_tickets():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    allTheTickets = ticketInstance.view_all_my_closed_tickets(LoggedInUser)
    if g.username:
        return render_template('my_closed_tickets.html', 
        currentUser=LoggedInUser1, allTheTickets=allTheTickets)
    else:
        return render_template('index.html')


@app.route('/my_low_priority_and_overdue_tickets')
def my_low_priority_and_overdue_tickets():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    allTheTickets = ticketInstance.view_all_my_overdue_tickets(LoggedInUser)
    if g.username:
        return render_template('my_overdue_tickets.html', 
        currentUser=LoggedInUser1, allTheTickets=allTheTickets)
    else:
        return render_template('index.html')


@app.route('/all_open_and_overdue_tickets')
def all_open_and_overdue_tickets():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    allTheTickets = ticketInstance.view_all_open_tickets()
    if g.username:
        return render_template('open_tickets.html', 
        currentUser=LoggedInUser1, allTheTickets=allTheTickets)
    else:
        return render_template('index.html')

@app.route('/all_my_open_and_overdue_tickets')
def all_my_open_and_overdue_tickets():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    allTheTickets = ticketInstance.view_all_my_tickets(LoggedInUser1)
    if g.username:
        return render_template('my_tickets.html', 
        currentUser=LoggedInUser1, allTheTickets=allTheTickets)
    else:
        return render_template('index.html')


@app.route('/add_equipment', methods=['POST'])
def add_equipment():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    equipment_serial = request.form['equipment_serial']
    equipment_serial_id = request.form['equipment_serial_id']
    equipment_model = request.form['equipment_model']
    equipment_class = request.form['equipment_class']
    equipment_type = request.form['equipment_type']
    equipment_category = request.form['equipment_category']
    equipment_resolution = request.form['equipment_resolution']
    equipment_response = request.form['equipment_response']
    equipment_installation_date = request.form['equipment_installation_date']
    equipment_installation_address = request.form['equipment_installation_address']
    equipment_installation_city = request.form['equipment_installation_city']
    equipment_supplier = request.form['equipment_supplier']
    if g.username:
        equipmentInstance.add_equipment(equipment_serial,equipment_serial_id,equipment_model,equipment_class,
        equipment_type,equipment_category,equipment_resolution,equipment_response,equipment_installation_date,
        equipment_installation_address,equipment_installation_city,equipment_supplier)
        return render_template('new_equipment.html',currentUser=LoggedInUser1)
    return redirect(url_for('index'))

@app.route('/upload/clients', methods = ['GET', 'POST'])
def upload_client():
   if request.method == 'POST':
      LoggedInUser = session['username']
      LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
      f = request.files['file']
      filename = secure_filename(f.filename)
      f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
      filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
      with open(filepath) as csv_file:
          data = csv.DictReader(csv_file)
          for item in data:
              customer_name = item['customer_name']
              customer_email = item['customer_email']
              customer_phone = item['customer_phone']
              customer_address = item['customer_address']
              customer_product = item['customer_product']
              customer_contact_person = item['contact_person']
              customer_contact_person_phone = item['contact_person_phone']
              custInstance.add_client(customer_name,customer_phone,customer_email,
              customer_address,customer_product,customer_contact_person,customer_contact_person_phone)
   if g.username:
       return render_template('view_clients.html',currentUser=LoggedInUser1)
   return redirect(url_for('index'))


@app.route('/upload/engineers', methods = ['GET', 'POST'])
def upload_engineers():
   if request.method == 'POST':
      LoggedInUser = session['username']
      LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
      f = request.files['engineers']
      filename = secure_filename(f.filename)
      f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
      filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
      with open(filepath) as csv_file:
          data = csv.DictReader(csv_file)
          for item in data:
              engineer_first_name = item['engineer_first_name']
              engineer_last_name = item['engineer_last_name']
              engineer_email = item['engineer_email']
              engineer_phone = item['engineer_phone']
              engineer_address = item['engineer_address']

              engineer_field_ATM_Value = 0

              engineer_field_AIR_Value = 0

              engineer_field_TEL_Value = 0

              engineersInstance.add_engineer(engineer_first_name,engineer_last_name,engineer_phone,engineer_email,engineer_address,engineer_field_ATM_Value,engineer_field_AIR_Value,engineer_field_TEL_Value)
   theReturnedEngineers = engineersInstance.get_all_engineers()
   if g.username:
       return render_template('view_engineers.html', allTheEngineers=theReturnedEngineers,currentUser=LoggedInUser1)
   return redirect(url_for('index'))

@app.route('/upload/equipments', methods = ['GET', 'POST'])
def upload_equipments():
   if request.method == 'POST':
      LoggedInUser = session['username']
      LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
      f = request.files['equipment']
      filename = secure_filename(f.filename)
      f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
      filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
      with open(filepath) as csv_file:
          data = csv.DictReader(csv_file)
          for item in data:
              equipment_serial = item['equipment_serial']
              equipment_serial_id = item['equipment_id']
              equipment_model = item['equipment_model']
              equipment_class = item['equipment_class']
              equipment_type = item['equipment_type']
              equipment_category = item['equipment_category']
              equipment_resolution = item['equipment_resolution']
              equipment_response = item['equipment_response']

            #   equipment_installation_date = item['equipment_installation_date']

              equipment_installation_address = request.form['equipment_installation_address']
              equipment_installation_city = item['equipment_installation_city']
              equipment_supplier = item['equipment_supplier']
              equipmentInstance.add_equipment(equipment_serial,equipment_serial_id,equipment_model,equipment_class,
              equipment_type,equipment_category,equipment_resolution,equipment_response,
              equipment_installation_address,equipment_installation_city,equipment_supplier)
    
   if g.username:
       return render_template('new_equipment.html',currentUser=LoggedInUser1)
   return redirect(url_for('index'))

def send_email_alerts(subject,recipients,body):
    with app.app_context():
        try:
            message = Message(subject=subject, sender=("Zubacx Call-Center", "zubacxnotification@gmail.com"), recipients=recipients, body=body)
            mail.send(message)
            print("Message sent successfully")
        except Exception as e:
            print(e)

@app.route('/user/profile', methods=['POST'])
def update_user_profile():
    LoggedInUser = session['username']
    LoggedInUser1 = usersInstance.checkUserRights(LoggedInUser)
    user_first_name = request.form['user_first_name_profile']
    user_last_name = request.form['user_last_name_profile']
    user_email = request.form['user_email_profile']
    user_name = request.form['user_name_profile']
    user_password = request.form['user_password_profile']
    encryptedPassword =  sha256_crypt.encrypt(str(user_password))
    usersInstance.edit_user_profile(user_first_name,user_last_name,user_email,
    user_name,encryptedPassword)
    if g.username:
        return render_template('profile.html',currentUser=LoggedInUser1)
    return redirect(url_for('index'))
    

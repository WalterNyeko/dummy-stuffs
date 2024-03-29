from app.database.connectDB import DatabaseConnectivity
from flask import flash, session
import datetime
import psycopg2
from app.users.users_model import Users

usersInstance = Users()

dbInstance = DatabaseConnectivity()
class Tickets:
    def add_ticket(self,ticket_assigned_to,ticket_opening_time,
        ticket_status,ticket_overdue_time,ticket_planned_visit_date,ticket_actual_visit_date,
        ticket_client,ticket_po_number,ticket_wo_type,ticket_reason,
        ticket_priority,username,ticket_type,ticket_revisited_value,ticket_site_id):
        try:
            conn = dbInstance.connectToDatabase()
            cur = conn.cursor()
            sql = """
            INSERT INTO tickets(ticket_assigned_to,ticket_opening_time,
            ticket_status,ticket_overdue_time,ticket_planned_visit_date,ticket_actual_visit_date,
            ticket_client,ticket_po_number,ticket_wo_type,ticket_reason,
            ticket_priority,username,ticket_type,
            ticket_revisited,ticket_site_id) VALUES(
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """
            cur.execute(sql,(ticket_assigned_to,ticket_opening_time,
            ticket_status,ticket_overdue_time,ticket_planned_visit_date,ticket_actual_visit_date,
            ticket_client,ticket_po_number,ticket_wo_type,ticket_reason,
            ticket_priority,username,ticket_type,ticket_revisited_value,ticket_site_id))
            conn.commit()
            flash('Ticket Opened Successfully','success')
        except(Exception, psycopg2.DatabaseError) as e:
            print(e)
            flash('Error submiting the data to database','danger')

    def sqlStatment(self):
            self.sql = """
            SELECT ticket_id,ticket_reason,ticket_assigned_to,ticket_client,
            CASE WHEN TIMESTAMPDIFF(MINUTE,ticket_overdue_time,NOW())>0 
            THEN CONCAT('Expired at ','',ticket_overdue_time) ELSE 
            CONCAT('Expires at ','',ticket_overdue_time) END AS Overdue,
            CASE WHEN ticket_status='Closed' 
            THEN CONCAT(ticket_status,' (',ticket_closing_time,')') 
            WHEN ticket_status='Open' AND TIMESTAMPDIFF(MINUTE,ticket_overdue_time,NOW())>0 AND TIMESTAMPDIFF(MINUTE,ticket_overdue_time,NOW())<60 
            THEN CONCAT('Overdue ','( Late By ',TIMESTAMPDIFF(MINUTE,ticket_overdue_time,NOW()),' Minutes)') 
            
            WHEN ticket_status='Open' AND TIMESTAMPDIFF(MINUTE,ticket_overdue_time,NOW())>59 AND TIMESTAMPDIFF(MINUTE,ticket_overdue_time,NOW())<1440 
            THEN CONCAT('Overdue ','( Late By ',TIMESTAMPDIFF(HOUR,ticket_overdue_time,NOW()),' Hours ',TIMESTAMPDIFF(MINUTE,ticket_overdue_time,NOW())%60, ' Minutes)')

            WHEN ticket_status='Open' AND TIMESTAMPDIFF(MINUTE,ticket_overdue_time,NOW())>1439 
            THEN CONCAT('Overdue ','( Late By ',TIMESTAMPDIFF(DAY,ticket_overdue_time,NOW()),' Days ',TIMESTAMPDIFF(HOUR,ticket_overdue_time,NOW())%24, ' Hours ',TIMESTAMPDIFF(MINUTE,ticket_overdue_time,NOW())%60, ' Minutes)')

            ELSE ticket_status END AS Ticket, ticket_priority, CASE WHEN ticket_type=1 THEN 'ATM Ticket' WHEN ticket_type=2 THEN 'Airport Ticket' WHEN ticket_type=3 THEN 'Telecom Ticket' WHEN ticket_type=4 
            THEN 'Fleet Ticket' ELSE 'Unknown Ticket' END AS ticket_types from tickets
            """
            return self.sql



    def view_all_tickets(self):
        try:
            current_user = usersInstance.checkUserAccount(session['username'])
            conn = dbInstance.connectToDatabase()
            cur = conn.cursor()
            theSql = Tickets().sqlStatment()
            print(current_user[1])
            # For Staffs
            if current_user[0] == 0:
                finalSQL = theSql + " ORDER BY ticket_id DESC"
            # For Clients
            else:
                finalSQL = theSql + """ WHERE ticket_client="{}" ORDER BY ticket_id DESC""".format(current_user[1])
            
            cur.execute(finalSQL)
            self.theTickets = cur.fetchall()
            return self.theTickets
        except:
            return


    def view_all_my_tickets(self,current_user):
        try:
            conn = dbInstance.connectToDatabase()
            cur = conn.cursor()
            theSql = Tickets().sqlStatment()
            theWhere = """ Where username="{}" ORDER BY ticket_id DESC""".format(current_user)
            cur.execute(theSql+theWhere)
            self.theTickets = cur.fetchall()
            return self.theTickets
        except(Exception, psycopg2.DatabaseError) as e:
            print(e)

    def view_all_closed_tickets(self):
        try:
            conn = dbInstance.connectToDatabase()
            current_user = usersInstance.checkUserAccount(session['username'])
            cur = conn.cursor()
            theSql = Tickets().sqlStatment()
            theStatus = "Closed"
            if current_user[0] == 0:
                theWhere = """ Where ticket_status="{}" ORDER BY ticket_id DESC""".format(theStatus)
            else:
                theWhere = """ Where ticket_status="{}" AND ticket_client="{}" ORDER BY ticket_id DESC""".format(theStatus, current_user[1])

            cur.execute(theSql+theWhere)

            self.theTickets = cur.fetchall()
            return self.theTickets
        except(Exception, psycopg2.DatabaseError) as e:
            print(e)
    
    def view_all_my_closed_tickets(self,current_user):
        try:
            conn = dbInstance.connectToDatabase()
            cur = conn.cursor()
            theSql = Tickets().sqlStatment()
            theStatus = "Closed"
            theWhere = """ Where ticket_status="{}" AND username="{}" ORDER BY ticket_id DESC""".format(theStatus,current_user)
            cur.execute(theSql+theWhere)
            self.theTickets = cur.fetchall()
            return self.theTickets
        except(Exception, psycopg2.DatabaseError) as e:
            print(e)

    def view_all_open_tickets(self):
        try:
            conn = dbInstance.connectToDatabase()
            current_user = usersInstance.checkUserAccount(session['username'])
            cur = conn.cursor()
            theSql = Tickets().sqlStatment()
            theStatus = "Open"
            if current_user[0] == 0:
                theWhere = """ Where ticket_status="{}" ORDER BY ticket_id DESC""".format(theStatus)
            else:
                theWhere = """ Where ticket_status="{}" AND ticket_client="{}" ORDER BY ticket_id DESC""".format(theStatus, current_user[1])

            cur.execute(theSql+theWhere)
            self.theTickets = cur.fetchall()
            return self.theTickets
        except(Exception, psycopg2.DatabaseError) as e:
            print(e)

    def view_all_my_open_tickets(self,current_user):
        try:
            conn = dbInstance.connectToDatabase()
            cur = conn.cursor()
            theSql = Tickets().sqlStatment()
            theStatus = "Open"
            theWhere = """ Where ticket_status="{}" AND username="{}" ORDER BY ticket_id DESC""".format(theStatus,current_user)
            cur.execute(theSql+theWhere)
            self.theTickets = cur.fetchall()
            return self.theTickets
        except(Exception, psycopg2.DatabaseError) as e:
            print(e)

    def view_all_tickets_due_in_2_hours(self):
        try:
            conn = dbInstance.connectToDatabase()
            current_user = usersInstance.checkUserAccount(session['username'])
            cur = conn.cursor()
            theSql = Tickets().sqlStatment()
            if current_user[0] == 0:
                theWhere = " Where TIMESTAMPDIFF(HOUR,ticket_overdue_time,NOW())<2 AND TIMESTAMPDIFF(HOUR,ticket_overdue_time,NOW())>0 ORDER BY ticket_id DESC"
            else:
                theWhere = """ Where TIMESTAMPDIFF(HOUR,ticket_overdue_time,NOW())<2 AND TIMESTAMPDIFF(HOUR,ticket_overdue_time,NOW())>0 AND ticket_client="{}" ORDER BY ticket_id DESC""".format(current_user[1])

            cur.execute(theSql+theWhere)
            self.theTickets = cur.fetchall()
            return self.theTickets
        except(Exception, psycopg2.DatabaseError) as e:
            print(e)

    def view_all_my_tickets_due_in_2_hours(self,current_user):
        try:
            conn = dbInstance.connectToDatabase()
            cur = conn.cursor()
            theSql = Tickets().sqlStatment()
            theWhere = """ Where TIMESTAMPDIFF(HOUR,ticket_overdue_time,NOW())<2 AND TIMESTAMPDIFF(HOUR,ticket_overdue_time,NOW())>0 AND username="{}" ORDER BY ticket_id DESC""".format(current_user)
            cur.execute(theSql+theWhere)
            self.theTickets = cur.fetchall()
            return self.theTickets
        except(Exception, psycopg2.DatabaseError) as e:
            print(e)

    def view_all_tickets_due_in_1_hour(self):
        try:
            conn = dbInstance.connectToDatabase()
            current_user = usersInstance.checkUserAccount(session['username'])
            cur = conn.cursor()
            theSql = Tickets().sqlStatment()
            if current_user[0] == 0:
                theWhere = " Where TIMESTAMPDIFF(HOUR,ticket_overdue_time,NOW())<1 AND TIMESTAMPDIFF(HOUR,ticket_overdue_time,NOW())>0 ORDER BY ticket_id DESC"           
            else:
                theWhere = """ Where TIMESTAMPDIFF(HOUR,ticket_overdue_time,NOW())<1 AND TIMESTAMPDIFF(HOUR,ticket_overdue_time,NOW())>0 AND ticket_client="{}" ORDER BY ticket_id DESC""".format(current_user[1])           
            cur.execute(theSql+theWhere)
            self.theTickets = cur.fetchall()
            return self.theTickets
        except(Exception, psycopg2.DatabaseError) as e:
            print(e)
    
    def view_all_my_tickets_due_in_1_hour(self,current_user):
        try:
            conn = dbInstance.connectToDatabase()
            cur = conn.cursor()
            theSql = Tickets().sqlStatment()
            theWhere = """ Where TIMESTAMPDIFF(HOUR,ticket_overdue_time,NOW())<1 AND TIMESTAMPDIFF(HOUR,ticket_overdue_time,NOW())>0 AND username="{}" ORDER BY ticket_id DESC""".format(current_user)
            cur.execute(theSql+theWhere)
            self.theTickets = cur.fetchall()
            return self.theTickets
        except(Exception, psycopg2.DatabaseError) as e:
            print(e)

    def view_all_overdue_tickets(self):
        try:
            conn = dbInstance.connectToDatabase()
            current_user = usersInstance.checkUserAccount(session['username'])
            cur = conn.cursor()
            theSql = Tickets().sqlStatment()
            if current_user[0] == 0:
                theWhere = " Where TIMESTAMPDIFF(HOUR,ticket_overdue_time,NOW())<0 AND ticket_complete_time IS NULL ORDER BY ticket_id DESC"
            else:
                theWhere = """ Where TIMESTAMPDIFF(HOUR,ticket_overdue_time,NOW())<0 AND ticket_complete_time IS NULL AND ticket_client="{}" ORDER BY ticket_id DESC""".format(current_user[1])

            cur.execute(theSql+theWhere)
            self.theTickets = cur.fetchall()
            return self.theTickets
        except(Exception, psycopg2.DatabaseError) as e:
            print(e)

    def view_all_low_priority_tickets(self):
        try:
            conn = dbInstance.connectToDatabase()
            cur = conn.cursor()
            theSql = Tickets().sqlStatment()
            theWhere = " Where ticket_priority=%s ORDER BY ticket_id DESC"
            theLowPriority = "Low"
            cur.execute(theSql+theWhere,[theLowPriority])
            self.theTickets = cur.fetchall()
            return self.theTickets
        except(Exception, psycopg2.DatabaseError) as e:
            print(e)

    def view_all_my_overdue_tickets(self,current_user):
        try:
            
            conn = dbInstance.connectToDatabase()
            cur = conn.cursor()
            theSql = Tickets().sqlStatment()
            theWhere = """ Where TIMESTAMPDIFF(HOUR,ticket_overdue_time,NOW())<0 AND ticket_complete_time IS NULL AND username="{}" ORDER BY ticket_id DESC""".format(current_user)
            cur.execute(theSql+theWhere)
            self.theTickets = cur.fetchall()
            return self.theTickets
        except(Exception, psycopg2.DatabaseError) as e:
            print(e)
            
    def view_all_my_low_priority_tickets(self,current_user):
        try:
            conn = dbInstance.connectToDatabase()
            cur = conn.cursor()
            theSql = Tickets().sqlStatment()
            theLowPriority = "Low"
            theWhere = " Where ticket_priority=%s AND username=%s ORDER BY ticket_id DESC"
            cur.execute(theSql+theWhere,[theLowPriority,current_user])
            self.theTickets = cur.fetchall()
            return self.theTickets
        except(Exception, psycopg2.DatabaseError) as e:
            print(e)


    def edit_ticket(self,ticket_assigned_to,
    ticket_status,ticket_overdue_time,ticket_planned_visit_date,ticket_actual_visit_date,
    ticket_client,ticket_po_number,ticket_wo_type,ticket_reason,ticket_client_visit_note,
    ticket_priority,ticket_root_cause,
    ticket_action_taken,ticket_pending_reason,ticket_additional_note,ticket_site_id,ticket_closing_time,
    ticket_dispatch_time,ticket_arrival_time,ticket_start_time,ticket_complete_time,ticket_return_time,ticket_type,ticket_id):
        try:
            conn = dbInstance.connectToDatabase()
            cur = conn.cursor()
            sql = """
            UPDATE tickets SET ticket_assigned_to=%s,
            ticket_status=%s,ticket_overdue_time=%s,ticket_planned_visit_date=%s,ticket_actual_visit_date=%s,
            ticket_client=%s,ticket_po_number=%s,ticket_wo_type=%s,ticket_reason=%s,ticket_client_visit_note=%s,
            ticket_priority=%s,ticket_root_cause=%s,
            ticket_action_taken=%s,ticket_pending_reason=%s,ticket_additional_note=%s,ticket_site_id=%s,ticket_closing_time=%s,
            ticket_dispatch_time=%s,ticket_arrival_time=%s,ticket_start_time=%s,ticket_complete_time=%s,ticket_return_time=%s,ticket_type=%s WHERE ticket_id=%s
            """
            cur.execute(sql,(ticket_assigned_to,
            ticket_status,ticket_overdue_time,ticket_planned_visit_date,ticket_actual_visit_date,
            ticket_client,ticket_po_number,ticket_wo_type,ticket_reason,ticket_client_visit_note,
            ticket_priority,ticket_root_cause,
            ticket_action_taken,ticket_pending_reason,ticket_additional_note,ticket_site_id,ticket_closing_time,
            ticket_dispatch_time,ticket_arrival_time,ticket_start_time,ticket_complete_time,ticket_return_time,ticket_type,ticket_id))
            conn.commit()
            if ticket_status == "Closed":
                flash('Ticket Closed Successfully','success')
            else:
                flash('Ticket Edited Successfully','success')
        except:
            flash('Error submiting the data to database','danger')


    def delete_a_user(self, user_id):
        try:
            conn = dbInstance.connectToDatabase()
            cur = conn.cursor()
            cur.execute("DELETE FROM users WHERE user_id=%s",[user_id])
            conn.commit()
            flash('User Deleted Successfully','success')
        except:
            flash('Error deleteing user from database','danger')
    def delete_a_ticket(self, ticket_id):
        try:
            conn = dbInstance.connectToDatabase()
            cur = conn.cursor()
            cur.execute("DELETE FROM tickets WHERE ticket_id=%s",[ticket_id])
            conn.commit()
            flash('Ticket Deleted Successfully','success')
        except:
            flash('Error deleteing ticket from database','danger')

    def get_ticket_by_Id(self, ticket_id):
        try:
            conn = dbInstance.connectToDatabase()
            cur = conn.cursor()
            sql = """SELECT * FROM tickets WHERE ticket_id=%s"""
            cur.execute(sql,[ticket_id])
            self.theTicket = cur.fetchone()
            return self.theTicket
        except:
            flash('Error retrieving ticket from database','danger')

    def get_ticket_overdue_time_by_Id(self, ticket_id):
        try:
            conn = dbInstance.connectToDatabase()
            cur = conn.cursor()
            sql = """SELECT ticket_overdue_time FROM tickets WHERE ticket_id=%s"""
            cur.execute(sql,[ticket_id])
            self.theTicket = cur.fetchone()
            return self.theTicket
        except:
            flash('Error retrieving ticket from database','danger')


    def get_work_order_types(self):
        try:
            conn = dbInstance.connectToDatabase()
            cur = conn.cursor()
            sql = """SELECT work_order_type FROM work_orders"""
            cur.execute(sql)
            self.theTypes = cur.fetchall()
            return self.theTypes
        except:
            flash('Error retrieving work order types from database','danger')

    def get_engineers(self):
        try:
            conn = dbInstance.connectToDatabase()
            cur = conn.cursor()
            sql = """SELECT CONCAT(engineer_first_name, ' ', engineer_last_name) FROM engineers"""
            cur.execute(sql)
            self.theTypes = cur.fetchall()
            return self.theTypes
        except:
            flash('Error retrieving engineers from database','danger')

    def get_clients(self):
        try:
            conn = dbInstance.connectToDatabase()
            cur = conn.cursor()
            sql = """SELECT customer_name FROM customers"""
            cur.execute(sql)
            self.theTypes = cur.fetchall()
            return self.theTypes
        except:
            flash('Error retrieving customers from database','danger')
    
    def general_function(self, sql):
        try:
            conn = dbInstance.connectToDatabase()
            cur = conn.cursor()
            cur.execute(sql)
            self.theTypes = cur.fetchall()
            return self.theTypes
        except:
            flash('Error retrieving customers from database','danger')

    def get_ATM_running_tasks(self):
        current_user = usersInstance.checkUserAccount(session['username'])
        if current_user[0] == 0:
            self.ticket_counts = Tickets().general_function("SELECT COUNT(*) FROM tickets WHERE ticket_dispatch_time IS NOT NULL AND ticket_complete_time IS NULL AND ticket_type=1")
        else:
            self.ticket_counts = Tickets().general_function("""SELECT COUNT(*) FROM tickets WHERE ticket_dispatch_time IS NOT NULL AND ticket_complete_time IS NULL AND ticket_client="{}" AND ticket_type=1""".format(current_user[1]))
        return self.ticket_counts
    def get_Airport_running_tasks(self):
        current_user = usersInstance.checkUserAccount(session['username'])
        if current_user[0] == 0:
            self.ticket_counts = Tickets().general_function("SELECT COUNT(*) FROM tickets WHERE ticket_dispatch_time IS NOT NULL AND ticket_complete_time IS NULL AND ticket_type=2")
        else:
            self.ticket_counts = Tickets().general_function("""SELECT COUNT(*) FROM tickets WHERE ticket_dispatch_time IS NOT NULL AND ticket_complete_time IS NULL AND ticket_client="{}" AND ticket_type=2""".format(current_user[1]))
        return self.ticket_counts
    def get_Telecom_running_tasks(self):
        current_user = usersInstance.checkUserAccount(session['username'])
        if current_user[0] == 0:
            self.ticket_counts = Tickets().general_function("SELECT COUNT(*) FROM tickets WHERE ticket_dispatch_time IS NOT NULL AND ticket_complete_time IS NULL AND ticket_type=3")
        else:
            self.ticket_counts = Tickets().general_function("""SELECT COUNT(*) FROM tickets WHERE ticket_dispatch_time IS NOT NULL AND ticket_complete_time IS NULL AND ticket_client="{}" AND ticket_type=3""".format(current_user[1]))
        return self.ticket_counts
    def get_Fleet_running_tasks(self):
        current_user = usersInstance.checkUserAccount(session['username'])
        if current_user[0] == 0:
            self.ticket_counts = Tickets().general_function("SELECT COUNT(*) FROM tickets WHERE ticket_dispatch_time IS NOT NULL AND ticket_complete_time IS NULL AND ticket_type=4")
        else:
            self.ticket_counts = Tickets().general_function("""SELECT COUNT(*) FROM tickets WHERE ticket_dispatch_time IS NOT NULL AND ticket_complete_time IS NULL AND ticket_client="{}" AND ticket_type=4""".format(current_user[1]))
        return self.ticket_counts

    def get_ATM_completed_tasks(self):
        current_user = usersInstance.checkUserAccount(session['username'])
        if current_user[0] == 0:
            self.ticket_counts = Tickets().general_function("SELECT COUNT(*) FROM tickets WHERE ticket_dispatch_time IS NOT NULL AND ticket_complete_time IS NOT NULL AND ticket_type=1")
        else:
            self.ticket_counts = Tickets().general_function("""SELECT COUNT(*) FROM tickets WHERE ticket_dispatch_time IS NOT NULL AND ticket_complete_time IS NOT NULL AND ticket_client="{}" AND ticket_type=1""".format(current_user[1]))
        return self.ticket_counts
    def get_Airport_completed_tasks(self):
        current_user = usersInstance.checkUserAccount(session['username'])
        if current_user[0] == 0:
            self.ticket_counts = Tickets().general_function("SELECT COUNT(*) FROM tickets WHERE ticket_dispatch_time IS NOT NULL AND ticket_complete_time IS NOT NULL AND ticket_type=2")
        else:
            self.ticket_counts = Tickets().general_function("""SELECT COUNT(*) FROM tickets WHERE ticket_dispatch_time IS NOT NULL AND ticket_complete_time IS NOT NULL AND ticket_client="{}" AND ticket_type=2""".format(current_user[1]))
        return self.ticket_counts
    def get_Telecom_completed_tasks(self):
        current_user = usersInstance.checkUserAccount(session['username'])
        if current_user[0] == 0:
            self.ticket_counts = Tickets().general_function("SELECT COUNT(*) FROM tickets WHERE ticket_dispatch_time IS NOT NULL AND ticket_complete_time IS NOT NULL AND ticket_type=3")
        else:
            self.ticket_counts = Tickets().general_function("""SELECT COUNT(*) FROM tickets WHERE ticket_dispatch_time IS NOT NULL AND ticket_complete_time IS NOT NULL AND ticket_client="{}" AND ticket_type=3""".format(current_user[1]))
        return self.ticket_counts
    def get_Fleet_completed_tasks(self):
        current_user = usersInstance.checkUserAccount(session['username'])
        if current_user[0] == 0:
            self.ticket_counts = Tickets().general_function("SELECT COUNT(*) FROM tickets WHERE ticket_dispatch_time IS NOT NULL AND ticket_complete_time IS NOT NULL AND ticket_type=4")
        else:
            self.ticket_counts = Tickets().general_function("""SELECT COUNT(*) FROM tickets WHERE ticket_dispatch_time IS NOT NULL AND ticket_complete_time IS NOT NULL AND ticket_client="{}" AND ticket_type=4""".format(current_user[1]))
        return self.ticket_counts

    def setOverdueSQL(self):
        current_user = usersInstance.checkUserAccount(session['username'])
        if current_user[0] == 0:
            self.sql = "SELECT COUNT(*) FROM tickets WHERE TIMESTAMPDIFF(HOUR,ticket_overdue_time,NOW())<1 AND TIMESTAMPDIFF(HOUR,ticket_overdue_time,NOW())>0 AND"
        else:
            self.sql = """SELECT COUNT(*) FROM tickets WHERE TIMESTAMPDIFF(HOUR,ticket_overdue_time,NOW())<1 AND TIMESTAMPDIFF(HOUR,ticket_overdue_time,NOW())>0 AND ticket_client="{}" AND""".format(current_user[1])

        return self.sql

    def setDisrespectedSQL(self):
        current_user = usersInstance.checkUserAccount(session['username'])
        if current_user[0] == 0:
            self.sql = "SELECT COUNT(*) FROM tickets WHERE TIMESTAMPDIFF(HOUR,ticket_overdue_time,NOW())>0 AND ticket_complete_time IS NULL AND"
        else:
            self.sql = """SELECT COUNT(*) FROM tickets WHERE TIMESTAMPDIFF(HOUR,ticket_overdue_time,NOW())>0 AND ticket_complete_time IS NULL AND ticket_client="{}" AND""".format(current_user[1])

        return self.sql

    def get_ATM_due_soon_tasks(self):
        sql = Tickets().setOverdueSQL()
        finalSQL =sql + " ticket_type=1"
        self.ticket_counts = Tickets().general_function(finalSQL)
        return self.ticket_counts
    def get_Airport_due_soon_tasks(self):
        sql = Tickets().setOverdueSQL()
        finalSQL =sql + " ticket_type=2"
        self.ticket_counts = Tickets().general_function(finalSQL)
        return self.ticket_counts
    def get_Telecom_due_soon_tasks(self):
        sql = Tickets().setOverdueSQL()
        finalSQL =sql + " ticket_type=3"
        self.ticket_counts = Tickets().general_function(finalSQL)
        return self.ticket_counts
    def get_Fleet_due_soon_tasks(self):
        sql = Tickets().setOverdueSQL()
        finalSQL =sql + " ticket_type=4"
        self.ticket_counts = Tickets().general_function(finalSQL)
        return self.ticket_counts


    def get_ATM_overdue_tasks(self):
        sql = Tickets().setDisrespectedSQL()
        finalSQL =sql + " ticket_type=1"
        print(finalSQL)
        self.ticket_counts = Tickets().general_function(finalSQL)
        return self.ticket_counts
    def get_Airport_overdue_tasks(self):
        sql = Tickets().setDisrespectedSQL()
        finalSQL =sql + " ticket_type=2"
        self.ticket_counts = Tickets().general_function(finalSQL)
        return self.ticket_counts
    def get_Telecom_overdue_tasks(self):
        sql = Tickets().setDisrespectedSQL()
        finalSQL =sql + " ticket_type=3"
        self.ticket_counts = Tickets().general_function(finalSQL)
        return self.ticket_counts
    def get_Fleet_overdue_tasks(self):
        sql = Tickets().setDisrespectedSQL()
        finalSQL =sql + " ticket_type=4"
        self.ticket_counts = Tickets().general_function(finalSQL)
        return self.ticket_counts


    def get_tickets_for_reports(self):
        current_user = usersInstance.checkUserAccount(session['username'])
        if current_user[0] == 0:
            self.ticket_counts = Tickets().general_function("""
            SELECT ticket_id,ticket_po_number,ticket_status,
            ticket_opening_time,ticket_site_id,ticket_client,
            CASE WHEN ticket_type=1 THEN 'ATM Product' WHEN ticket_type=2
            THEN 'Airport Product' WHEN ticket_type=3 THEN 'Telecom Product'
            WHEN ticket_type=4 THEN 'Fleet Product' ELSE 'Unknown Product' 
            END AS ticket_types,ticket_reason,ticket_root_cause,ticket_assigned_to,
            ticket_dispatch_time,ticket_arrival_time,ticket_start_time,ticket_complete_time,
            ticket_return_time,ticket_part_used,ticket_revisited,ticket_part_returned FROM tickets 
            ORDER BY ticket_opening_time DESC""")
        else:
            self.ticket_counts = Tickets().general_function("""
            SELECT ticket_id,ticket_po_number,ticket_status,
            ticket_opening_time,ticket_site_id,ticket_client,
            CASE WHEN ticket_type=1 THEN 'ATM Product' WHEN ticket_type=2
            THEN 'Airport Product' WHEN ticket_type=3 THEN 'Telecom Product'
            WHEN ticket_type=4 THEN 'Fleet Product' ELSE 'Unknown Product' 
            END AS ticket_types,ticket_reason,ticket_root_cause,ticket_assigned_to,
            ticket_dispatch_time,ticket_arrival_time,ticket_start_time,ticket_complete_time,
            ticket_return_time,ticket_part_used,ticket_revisited,ticket_part_returned 
            WHERE ticket_client="{}" FROM tickets ORDER BY ticket_opening_time DESC""".format(current_user[1]))
       
        return self.ticket_counts

    def number_of_open_atm(self):
        try:
            conn = dbInstance.connectToDatabase()
            current_user = usersInstance.checkUserAccount(session['username'])
            cur = conn.cursor()
            ticket_status = "Open"
            ticket_type = 1
            if current_user[0] == 0:
                theSql = """Select count(*) from tickets Where ticket_status="{}" and ticket_type="{}" """.format(ticket_status, ticket_type)
            else:
                theSql = """Select count(*) from tickets Where ticket_status="{}" and ticket_type="{}" and ticket_client="{}" """.format(ticket_status, ticket_type,current_user[1])

            cur.execute(theSql)
            self.theTickets = cur.fetchall()
            return self.theTickets
        except(Exception, psycopg2.DatabaseError) as e:
            print(e)

    def number_of_open_air(self):
        try:
            conn = dbInstance.connectToDatabase()
            current_user = usersInstance.checkUserAccount(session['username'])
            cur = conn.cursor()
            ticket_status = "Open"
            ticket_type = 2
            if current_user[0] == 0:
                theSql = """Select count(*) from tickets Where ticket_status="{}" and ticket_type="{}" """.format(ticket_status, ticket_type)
            else:
                theSql = """Select count(*) from tickets Where ticket_status="{}" and ticket_type="{}" and ticket_client="{}" """.format(ticket_status, ticket_type,current_user[1])

            cur.execute(theSql)
            self.theTickets = cur.fetchall()
            return self.theTickets
        except(Exception, psycopg2.DatabaseError) as e:
            print(e)

    def number_of_open_tel(self):
        try:
            conn = dbInstance.connectToDatabase()
            current_user = usersInstance.checkUserAccount(session['username'])
            cur = conn.cursor()
            ticket_status = "Open"
            ticket_type = 3
            if current_user[0] == 0:
                theSql = """Select count(*) from tickets Where ticket_status="{}" and ticket_type="{}" """.format(ticket_status, ticket_type)
            else:
                theSql = """Select count(*) from tickets Where ticket_status="{}" and ticket_type="{}" and ticket_client="{}" """.format(ticket_status, ticket_type,current_user[1])

            cur.execute(theSql)
            self.theTickets = cur.fetchall()
            return self.theTickets
        except(Exception, psycopg2.DatabaseError) as e:
            print(e)

    def number_of_open_fle(self):
        try:
            conn = dbInstance.connectToDatabase()
            current_user = usersInstance.checkUserAccount(session['username'])
            cur = conn.cursor()
            ticket_status = "Open"
            ticket_type = 4
            if current_user[0] == 0:
                theSql = """Select count(*) from tickets Where ticket_status="{}" and ticket_type="{}" """.format(ticket_status, ticket_type)
            else:
                theSql = """Select count(*) from tickets Where ticket_status="{}" and ticket_type="{}" and ticket_client="{}" """.format(ticket_status, ticket_type,current_user[1])

            cur.execute(theSql)
            self.theTickets = cur.fetchall()
            return self.theTickets
        except(Exception, psycopg2.DatabaseError) as e:
            print(e)

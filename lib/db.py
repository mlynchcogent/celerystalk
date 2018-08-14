import sqlite3
from sqlite3 import Error

CONNECTION = sqlite3.connect("csdb.sqlite3")
CUR = CONNECTION.cursor()

def create_task_table():
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """

    sql_create_tasks_table = """ CREATE TABLE IF NOT EXISTS tasks (
                                    id INTEGER PRIMARY KEY,
                                    task_id text NOT NULL,
                                    pid integer,                                    
                                    command text NOT NULL,
                                    ip text NOT NULL,                                
                                    status text NOT NULL,
                                    workspace text NOT NULL,
                                    start_time text,
                                    run_time text                                     
                                   ); """

    try:
        CUR.execute(sql_create_tasks_table)
        CONNECTION.commit()
    except Error as e:
        print(e)


def create_workspace_table():
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """

    sql_create_workspace_table = """ CREATE TABLE IF NOT EXISTS workspace (
                                        name text PRIMARY KEY,
                                        creation_date text NOT NULL
                                    ); """

    try:
        CUR.execute(sql_create_workspace_table)
        CONNECTION.commit()
    except Error as e:
        print(e)


def create_path_table():
    sql_create_paths_table = """ CREATE TABLE IF NOT EXISTS paths (
                                        id integer PRIMARY KEY,
                                        ip text NOT NULL,
                                        port int NOT NULL,
                                        path text NOT NULL UNIQUE,
                                        submitted int,
                                        workspace text NOT NULL
                                    ); """

    try:
        CUR.execute(sql_create_paths_table)
        CONNECTION.commit()
    except Error as e:
        print(e)

def create_services_table():
    sql_create_services_table = """ CREATE TABLE IF NOT EXISTS services (
                                        id INTEGER PRIMARY KEY,
                                        ip text NOT NULL,
                                        port int NOT NULL,
                                        proto text NOT NULL,
                                        service text,                                        
                                        workspace text
                                    ); """
    CUR.execute(sql_create_services_table)

    try:
        CUR.execute(sql_create_services_table)
        CONNECTION.commit()
    except Error as e:
        print(e)


def create_vhosts_table():

    sql_create_vhosts_table = """ CREATE TABLE IF NOT EXISTS vhosts (
                                        id INTEGER PRIMARY KEY,
                                        ip text,
                                        vhost text NOT NULL UNIQUE,
                                        in_scope int NOT NULL,
                                        submitted int NOT NULL,                                                                                
                                        workspace text
                                    ); """

    try:
        CUR.execute(sql_create_vhosts_table)
        CONNECTION.commit()
    except Error as e:
        print(e)



def create_workspace(workspace):
    """

    :param workspace:
    :return:
    """
    sql = ''' INSERT INTO workspace(name,creation_date)
              VALUES(?,?) '''
    CUR.execute(sql, workspace)
    CONNECTION.commit()
    #return cur.lastrowid

def create_task(task):
    """

    :param workspace:
    :return:
    """
    sql = ''' INSERT INTO tasks(task_id, pid, command, ip, status, workspace)
              VALUES(?,?,?,?,?,?) '''

    CUR.execute(sql, task)
    CONNECTION.commit()
    #return cur.lastrowid

def create_service(db_service):
    """

    :param workspace:
    :return:
    """
    sql = ''' INSERT INTO services(ip,port,proto,service,workspace)
              VALUES(?,?,?,?,?) '''
    CUR.execute(sql, db_service)
    CONNECTION.commit()


def create_vhost(db_vhost):
    """

    :param workspace:
    :return:
    """
    sql = ''' INSERT OR IGNORE INTO vhosts(ip,vhost,in_scope,submitted,workspace)
              VALUES(?,?,?,?,?) '''
    CUR.execute(sql, db_vhost)
    CONNECTION.commit()


def insert_new_path(db_path):
    """

    :param db_path:
    :return:
    """
    sql = '''INSERT OR IGNORE INTO paths(ip,port,path,submitted,workspace)
              VALUES(?,?,?,?,?)  '''
    CUR.execute(sql, db_path)
    CONNECTION.commit()



def get_completed_task_count(workspace):
    CUR.execute("SELECT count(*) FROM tasks where status = ? AND workspace = ?", ("COMPLETED", workspace))
    completed_count = CUR.fetchall()
    CONNECTION.commit()
    return completed_count

def get_pending_task_count(workspace):
    CUR.execute("SELECT count(*) FROM tasks where status = ? AND workspace = ?", ("SUBMITTED", workspace))
    pending_count = CUR.fetchall()
    CONNECTION.commit()
    return pending_count

def get_completed_tasks(workspace):
    CUR.execute("SELECT pid,command,run_time,ip FROM tasks where status = ? AND workspace = ?", ("COMPLETED", workspace))
    completed_tasks = CUR.fetchall()
    CONNECTION.commit()
    return completed_tasks

def get_all_completed_tasks():
    CUR.execute("SELECT command,workspace FROM tasks where status = ?", ("COMPLETED"))
    all_tasks = CUR.fetchall()
    CONNECTION.commit()
    return all_tasks

def get_cancelled_tasks(workspace):
    CUR.execute("SELECT id,command FROM tasks where status = ? AND workspace = ?", ("CANCELLED", workspace))
    cancelled_tasks = CUR.fetchall()
    CONNECTION.commit()
    return cancelled_tasks

def get_paused_tasks(workspace):
    CUR.execute("SELECT id,command FROM tasks where status = ? AND workspace = ?", ("PAUSED", workspace))
    paused_tasks = CUR.fetchall()
    CONNECTION.commit()
    return paused_tasks

def get_task_id_status_pid(id):
    CUR.execute("SELECT id,task_id,status,pid FROM tasks where id = ?", (id,))
    task_id_status_pid = CUR.fetchall()
    CONNECTION.commit()
    return task_id_status_pid

def get_pending_tasks(workspace,ip=None):
    if ip:
        CUR.execute("SELECT id,command FROM tasks where status = ? AND workspace = ? AND ip = ?",
                    ("SUBMITTED", workspace,ip))
    else:
        CUR.execute("SELECT id,command FROM tasks where status = ? AND workspace = ?",
                    ("SUBMITTED", workspace))
    pending_count = CUR.fetchall()
    CONNECTION.commit()
    return pending_count

def get_running_tasks(workspace,ip=None):
    if ip:
        CUR.execute("SELECT id,command,start_time,pid FROM tasks where status = ? AND workspace = ? AND ip = ?",
                    ("STARTED", workspace,ip))
    else:
        CUR.execute("SELECT id,command,start_time,pid FROM tasks where status = ? AND workspace = ?",
                    ("STARTED", workspace))
    running_rows = CUR.fetchall()
    CONNECTION.commit()
    return running_rows


def get_paused_tasks(workspace,ip=None):
    if ip:
        CUR.execute("SELECT id,command,start_time,pid FROM tasks where status = ? AND workspace = ?  AND ip = ?",
                    ("PAUSED", workspace,ip))
    else:
        CUR.execute("SELECT id,command,start_time,pid FROM tasks where status = ? AND workspace = ?",
                    ("PAUSED", workspace))
    paused_rows = CUR.fetchall()
    return paused_rows


def get_service(ip,port,protocol,workspace):
    CUR.execute("SELECT * FROM services WHERE ip=? AND port=? and proto=? and workspace=?", (ip,port,protocol,workspace))
    service_row = CUR.fetchall()
    CONNECTION.commit()
    return service_row

def get_all_services(workspace):
    CUR.execute("SELECT * FROM services WHERE workspace=?", (workspace,))
    service_rows = CUR.fetchall()
    CONNECTION.commit()
    return service_rows

def get_all_services_for_ip(ip,workspace):
    CUR.execute("SELECT * FROM services WHERE ip=? AND workspace=?", (ip,workspace))
    service_rows = CUR.fetchall()
    CONNECTION.commit()
    return service_rows

def get_unique_hosts(workspace):
    CUR.execute("SELECT DISTINCT ip FROM services WHERE workspace=?", (workspace,))
    host_rows = CUR.fetchall()
    CONNECTION.commit()
    return host_rows

def get_inscope_unsubmitted_vhosts(workspace):
    CUR.execute("SELECT vhost FROM vhosts WHERE in_scope=? AND submitted=? AND workspace=?", (1,0,workspace))
    scannable_vhosts = CUR.fetchall()
    CONNECTION.commit()
    return scannable_vhosts

def get_vhost_ip(scannable_vhost,workspace):
    CUR.execute("SELECT ip FROM vhosts WHERE vhost=? AND workspace=?", (scannable_vhost,workspace))
    ip = CUR.fetchall()
    CONNECTION.commit()
    return ip

def get_total_tasks(workspace):
    CUR.execute("SELECT count(*) FROM tasks where workspace = ?", (workspace,))
    total_count = CUR.fetchall()
    CONNECTION.commit()
    return total_count

def get_unsubmitted_paths(workspace):
    CUR.execute("SELECT path FROM paths WHERE workspace = ?" (workspace,))
    unsubmitted_paths = CUR.fetchall()
    CONNECTION.commit()
    return unsubmitted_paths


def update_task_status_started(status,task_id,pid,start_time):
    CUR.execute("UPDATE tasks SET status=?,pid=?,start_time=? WHERE task_id=?", (status,pid,start_time,task_id))
    CONNECTION.commit()


def update_task_status_completed(status,task_id,run_time):
    CUR.execute("UPDATE tasks SET status=?,run_time=? WHERE task_id=?", (status, run_time, task_id))
    CONNECTION.commit()


def update_task_status_cancelled(task_id):
    CUR.execute("UPDATE tasks SET status=? WHERE task_id=?", ("CANCELLED",task_id))
    CONNECTION.commit()


def update_task_status_paused(task_id):
    CUR.execute("UPDATE tasks SET status=? WHERE task_id=?", ("PAUSED",task_id))
    CONNECTION.commit()


def update_task_status_resumed(task_id):
    CUR.execute("UPDATE tasks SET status=? WHERE task_id=?", ("STARTED",task_id))
    CONNECTION.commit()


# def insert_new_path(path,b,workspace):
#
#     CUR.execute("INSERT OR IGNORE INTO path values (?,?,?)", (path,b,workspace))
#
#     CONNECTION.commit()

def update_path(path,submitted,workspace):
    CUR.execute("UPDATE paths SET submitted=? WHERE path=? AND workspace=?", (submitted,path,workspace))
    CONNECTION.commit()


def update_service(ip,port,proto,service,workspace):
    CUR.execute("UPDATE services SET service=? WHERE ip=? AND port=? AND proto=? AND workspace=?", (service,ip,port,proto,workspace))
    CONNECTION.commit()


def update_vhosts_submitted(ip,vhost,workspace,submitted):
    CUR.execute("UPDATE vhosts SET submitted=? WHERE ip=? AND vhost=? AND workspace=?", (submitted,ip,vhost,workspace))
    CONNECTION.commit()
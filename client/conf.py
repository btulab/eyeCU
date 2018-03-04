import configparser
import MySQLdb

creds = configparser.ConfigParser()
creds.read('db.cfg')

def dbconnection():

    db = MySQLdb.connect(host=creds.get('database', 'host'),
                     user=creds.get('database', 'user'),
                     passwd=creds.get('database', 'passwd'),
                     db=creds.get('database', 'db'))
    
    cur = db.cursor()
    return db,cur

def motd():
    return creds.get('motd', 'message')

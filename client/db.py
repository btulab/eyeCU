import configparser
import MySQLdb

dbcreds = configparser.ConfigParser()
dbcreds.read('db.cfg')

def connection():
    db = MySQLdb.connect(host=dbcreds.get('database', 'host'),
                     user=dbcreds.get('database', 'user'),
                     passwd=dbcreds.get('database', 'passwd'),
                     db=dbcreds.get('database', 'db'))

    cur = db.cursor()
    return db, cur 

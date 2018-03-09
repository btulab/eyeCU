from passlib.hash import pbkdf2_sha256
from conf import dbconnection
import configparser
import MySQLdb
import string, random, sys

def createUser(username, password):
    db,cur = dbconnection()

    # check if user already exists
    cur = db.cursor()
    cur.execute("SELECT COUNT(1) FROM Users WHERE email = %s;", [username])
    if cur.fetchone()[0]:
        print("%s already exists in database." % username)
        exit()

    # add a random salt
    salt = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(40))
    password = password + salt

    passhash = pbkdf2_sha256.encrypt(password, rounds=200000, salt_size=16)

    # insert into database
    query = "INSERT INTO Users(email,salt,hash) " \
             "VALUES(%s,%s,%s)"
    args = (username,salt,passhash)
    cur.execute(query,args)
    db.commit()

    # check database entry to verify
    # grab salt
    cur.execute("SELECT salt FROM Users WHERE email = %s;", [username])
    salt = cur.fetchall()

    # hash
    cur.execute("SELECT hash FROM Users WHERE email = %s;", [username])
    passhash = cur.fetchall()

def login(username,password):
    db,cur = dbconnection()
    cur.execute("SELECT COUNT(1) FROM Users WHERE email = %s;", [username])
    if cur.fetchone()[0]:
        cur.execute("SELECT salt FROM Users WHERE email = %s;", [username])
        salt = cur.fetchall()
        password = password + salt[0][0]
        cur.execute("SELECT hash FROM Users WHERE email = %s;", [username])
        passhash = cur.fetchall()
        cur.close()
        if pbkdf2_sha256.verify(password, passhash[0][0]):
            return True
        
    return False

if __name__ == '__main__':

    if len(sys.argv) != 3:
        print("Usage: python auth.py [username] [password]")
        print(sys.argv)
        quit()
    createUser(sys.argv[1], sys.argv[2])

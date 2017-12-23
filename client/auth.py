from passlib.hash import pbkdf2_sha256
import configparser
import MySQLdb
import string, random

dbcreds = configparser.ConfigParser()
dbcreds.read('db.cfg')
db = MySQLdb.connect(host=dbcreds.get('database', 'host'),
                     user=dbcreds.get('database', 'user'),
                     passwd=dbcreds.get('database', 'passwd'),
                     db=dbcreds.get('database', 'db'))

# credentials
username = "admin"
password = "morty"

# add a random salt
salt = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(40))
print(salt)
password = password + salt
print(password)

passhash = pbkdf2_sha256.encrypt(password, rounds=200000, salt_size=16)
print(passhash)

# insert into database
query = "INSERT INTO Users(email,salt,hash) " \
        "VALUES(%s,%s,%s)"
args = (username,salt,passhash)
cur = db.cursor()
cur.execute(query,args)
db.commit()

# check database entry to verify
# grab salt
cur.execute("SELECT salt FROM Users WHERE email = %s;", [username])
salt = cur.fetchall()
print("salt")
print(salt)
print(salt[0][0])

# hash
cur.execute("SELECT hash FROM Users WHERE email = %s;", [username])
passhash = cur.fetchall()
print("excess")
print(passhash[0][0])

print(pbkdf2_sha256.verify(password, passhash[0][0]))


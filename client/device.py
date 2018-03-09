from flask import request
import configparser
import MySQLdb
from flask_socketio import emit
from time import localtime, time, strftime
from conf import dbconnection

valid_keys = ["temperature", "co2", "pressure", "humidity", "altitude", "sound", "MAC", "voc", "light", "button", "motion"]

def add_data(last_update_dict,request):
	db,cur = dbconnection()
	insert_string_variables = ["deviceID", "timeRecieved"]
	for key in valid_keys:
		insert_string_variables.append(key)
	print(insert_string_variables)
	cur.execute("SELECT deviceID,name FROM Devices WHERE MAC=%s", [request.form['MAC']])
	device = cur.fetchall()
	if (len(device) > 1):
		print("Error: duplicate MAC -- " + request.form['MAC'])
		return "Error: duplicate MAC"
	deviceID = device[0][0]
	deviceName = device[0][1]
	insert_string_values = [int(deviceID), float(last_update_dict[request.form['MAC']])]
	insert_string_values = {"deviceID": int(deviceID), "timeRecieved": float(last_update_dict[request.form['MAC']])}
	for key in valid_keys:
		if key in request.form:
			if (key == "MAC"):
				insert_string_values[key] = str("'" + request.form[key] + "'")
			elif (key == "button" or key == "motion"):
				insert_string_values[key] = int(request.form[key])
			else:
				insert_string_values[key] = float(request.form[key])
		else:
			return "Error: all variables must be present"
	sql = "INSERT INTO Data (" + ",".join(insert_string_variables) + ") VALUES (%d,%f,%f,%f,%f,%f,%f,%f,%s,%f,%f,%d,%d)" % (insert_string_values['deviceID'], insert_string_values['timeRecieved'], insert_string_values['temperature'], insert_string_values['co2'], insert_string_values['pressure'], insert_string_values['humidity'], insert_string_values['altitude'], insert_string_values['sound'], insert_string_values['MAC'], insert_string_values['voc'], insert_string_values['light'], insert_string_values['button'], insert_string_values['motion'])
	cur.execute(sql)
	print("POST FROM -- " + request.form['MAC'])
	msg = ("Data recieved from %s <a href=\"/devices/%s\">(Device: %s)</a>" % (deviceName,deviceID,deviceID))
	db.commit()
	cur.close()
	return msg

def device_state(last_update_dict):
        devices = []
        db,cur = dbconnection()
        cur.execute("SELECT deviceID,name,MAC FROM Devices")
        for row in cur.fetchall():
                device_info = {'deviceID':row[0], 'name':row[1]}
                if (time() - last_update_dict[row[2]]) > (300 * 4):             #If the device has missed more than 4 updates
                        device_info['alive'] = False
                else:
                        device_info['alive'] = True
                devices.append(device_info)
        cur.close()
        return devices

def device_data():
    pass

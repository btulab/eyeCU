from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired

class ContactForm(FlaskForm):
    name = StringField("Name")
    email = StringField("Email")
    subject = StringField("Subject")
    message = StringField("Message")

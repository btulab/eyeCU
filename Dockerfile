FROM tiangolo/uwsgi-nginx-flask:python3.6

COPY ./client /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 5000
ENV FLASK_APP=app.py
CMD [ "python", "-m", "flask", "run", "--host=0.0.0.0" ]

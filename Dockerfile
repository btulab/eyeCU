FROM tiangolo/uwsgi-nginx-flask:python3.6

COPY ./client /app
WORKDIR /app
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["app.py"]

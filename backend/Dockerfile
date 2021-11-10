FROM python:3.8.5
WORKDIR /code
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY . .
CMD python manage.py runserver 0:8000

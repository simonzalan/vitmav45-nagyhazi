FROM python:3.8

ADD requirements.txt
RUN pip install -r /requirements.txt

ADD vitmav_nagyhazi.py

ENV PYTHONUNBUFFERED=1

CMD [ "python", "./vitmav_nagyhazi.py" ]
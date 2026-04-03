FROM python:3.9

WORKDIR /app
COPY . .

RUN pip install flask requests

EXPOSE 5000
CMD ["python", "app.py"]

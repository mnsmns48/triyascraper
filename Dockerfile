FROM python:3.11
WORKDIR /triyascraper
COPY requirements.txt /triyascraper
COPY . /triyascraper
RUN pip install -r requirements.txt
RUN playwright install --with-deps
CMD ["python", "main.py"]
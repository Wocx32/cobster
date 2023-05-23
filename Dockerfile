FROM alpine:3.17

WORKDIR /usr/src/app

RUN apk add --no-cache \
        python3 \
        py3-pip

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN echo "0 * * * * cd /usr/src/app && python3 main.py" | crontab -
CMD ["crond", "-f", "-d", "0", "-L", "/dev/stdout"]
FROM python:3.12-alpine

RUN pip3 install faker --break-system-packages

RUN mkdir -p /usr/share/nginx/html

COPY persona_gen.py /opt/persona_gen.py
COPY server.py /opt/server.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

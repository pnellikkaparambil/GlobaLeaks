FROM ubuntu:22.04

RUN apt update && apt install python3 python3-pip python3.10-venv curl -y

# node
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
RUN apt-get install -y nodejs

WORKDIR /globaleaks

COPY ./backend /globaleaks/backend

RUN pip3 install -r backend/requirements/requirements-bookworm.txt

COPY . .

WORKDIR /globaleaks/client
RUN npm install
RUN npm install -g grunt-cli

RUN grunt copy:sources

WORKDIR /globaleaks/backend

EXPOSE 8080
EXPOSE 8443

# USER globaleaks

CMD ["/usr/bin/python3", "bin/globaleaks", " -z", "-n"]

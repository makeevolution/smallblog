# Set base image
FROM python:3.9.21-slim-bookworm

ENV FLASK_APP blogging.py
ENV FLASK_CONFIG docker

# Do not use root; best practice for security
RUN useradd -m someuser && adduser someuser sudo
RUN passwd --delete someuser
USER someuser

# Where the application will be installed
WORKDIR /home/someuser/blogging

COPY requirements requirements
RUN pip install wheel 
# Install requirements
# Since we are using non root, any executables installed by pip (e.g. gunicorn) will be in this directory
ENV PATH "$PATH:~/.local/bin"
RUN pip install -r requirements/prod.txt

COPY app app
COPY migrations migrations
COPY blogging.py config.py boot.sh ./

EXPOSE 5000
# Use bash to run the shell file, so the [[]] syntax in boot.sh is recognized!
ENTRYPOINT ["bash","./boot.sh"]

# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: CC0-1.0

FROM httpd:2.4.52
EXPOSE 80
WORKDIR /code

# Base installation
RUN mkdir /var/run/apache2      &&  \
    apt-get update              &&  \
    apt-get install -y              \
        python3                     \
        python3-pip                 \
        libapache2-mod-wsgi-py3 &&  \
    apt-get auto-remove         &&  \
    rm -rf /var/lib/apt/lists/  &&  \
    pip install poetry

# Install python dependencies.
RUN poetry config virtualenvs.in-project true
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev --extras webserver

# Copy the webserver config
COPY ./webserver/httpd.conf  /usr/local/apache2/conf/httpd.conf
COPY webserver/ /var/www/html

# Copy the python project files and install them
COPY ./ ./
RUN poetry install --no-dev

# Apache runs as www-data per httpd.conf above
ARG GITHASH
ENV GITHASH="$GITHASH"
CMD GITHASH="$GITHASH" VENV="$(poetry env info -p)" httpd-foreground

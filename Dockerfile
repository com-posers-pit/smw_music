# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: CC0-1.0

FROM httpd:2.4.52
EXPOSE 80
WORKDIR /var/www/html

RUN mkdir /var/run/apache2      &&  \
    apt-get update              &&  \
    apt-get install -y              \
        python3                     \
        python3-pip                 \
        libapache2-mod-wsgi-py3 &&  \
    apt-get auto-remove         &&  \
    rm -rf /var/lib/apt/lists/  &&  \
    pip install poetry

COPY ./webserver/httpd.conf  /usr/local/apache2/conf/httpd.conf
COPY webserver/ /var/www/html
COPY ./ /tmp

RUN cd /tmp                                     && \
    poetry config virtualenvs.create false      && \
    poetry install --extras webserver

CMD httpd-foreground

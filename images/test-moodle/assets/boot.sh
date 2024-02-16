#!/bin/bash

timedatectl set-timezone Europe/Berlin

# on first boot: move MariaDB data to mounted volume
test ! -e /var/lib/mysql/mysql && cp -a /var/lib/mysql_backup/. /var/lib/mysql/

# make data base files accessible to all users
# (else, deleting the data base outside the container requires root privileges)
chown -R mysql:mysql /var/lib/mysql
chmod -R a+rwX /var/lib/mysql

# start MariaDB (starting this failed at first boot, because of missing /var/lib/mysql)
systemctl start mysql

# make Moodle data directory accessible to all users
# (www-data should suffice, but Moodle doc says 777)
chmod -R a+rwX /opt/moodledata

# make persistent config.php available to Moodle
test -e /opt/moodledata/config.php && test ! -e /var/www/html/moodle/config.php && cp /opt/moodledata/config.php /var/www/html/moodle/config.php && chmod 644 /var/www/html/moodle/config.php

#!/bin/bash

timedatectl set-timezone Europe/Berlin

# initialize Moodle on boot, if no data base exists
init_moodle () {

    # move directories to be persisted to mounted volumes
    cp -a /var/lib/mysql_original/. /var/lib/mysql/
    cp -a /opt/moodledata_original/. /opt/moodledata/
    cp -a /var/www/html/moodle_original/. /var/www/html/moodle/
    
    # start MariaDB (starting this failed at first boot, because of missing /var/lib/mysql)
    systemctl start mysql

    # create Moodle data base user and data base
    mysql -u root -e "CREATE DATABASE moodle DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    mysql -u root -e "CREATE USER moodleuser@localhost IDENTIFIED BY 'moodleuserpassword'"
    mysql -u root -e "GRANT SELECT,INSERT,UPDATE,DELETE,CREATE,CREATE TEMPORARY TABLES,DROP,INDEX,ALTER ON moodle.* TO moodleuser@localhost"
        
    # create Moodle's config.php
    cd /var/www/html/moodle/admin/cli
    php install.php \
        --wwwroot="$MOODLE_URL_DOMAIN$MOODLE_URL_PATH" \
        --dataroot=/opt/moodledata \
        --dbtype=mariadb \
        --dbuser=moodleuser \
        --dbpass=moodleuserpassword \
        --fullname="Test Moodle" \
        --shortname="Test" \
        --adminuser=admin \
        --adminpass=Admin123. \
        --adminemail="admin@no.where" \
        --agree-license \
        --skip-database \
        --non-interactive

    # add several option to config.php
    # - reverse proxy mode
    # - router configured
    # - SSL proxy mode
    # - debug output
    # - registerauth (to remove a warning on the login page, seems to be a bug in Moodle that this option is used although undefined)
    sed -i "s#'admin';#'admin';\n\$CFG->reverseproxy = true;\n\$CFG->routerconfigured = true;\n\$CFG->sslproxy = true;\n\$CFG->debugdisplay = true;\n\$CFG->debug = E_ALL;\n\$CFG->registerauth = '';#g" /var/www/html/moodle/config.php

    # create tables
    cd /var/www/html/moodle/admin/cli
    php install_database.php --adminpass=Admin123. --agree-license

}
test ! -e /var/lib/mysql/mysql && init_moodle

# make data base files accessible to all users
# (else, deleting the data base outside the container requires root privileges)
chown -R mysql:mysql /var/lib/mysql
chmod -R a+rwX /var/lib/mysql

# make Moodle data directory accessible to all users
# (www-data should suffice, but Moodle doc says 777)
chmod -R a+rwX /opt/moodledata

# make root the owner of Moodle files (seems to be not the case after install?!)
# make Moodle files readable for non-root users (www-data!)
chown -R root:root /var/www/html/moodle
chmod -R a+r /var/www/html/moodle

# write URL path to nginx config
sed -i "s#MOODLE_URL_PATH#$MOODLE_URL_PATH#g" /etc/nginx/sites-available/default

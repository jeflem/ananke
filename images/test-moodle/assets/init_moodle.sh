#!/bin/bash

read -p "URL of your Moodle container (e.g. http://192.168.178.28:9090): " url

# create Moodle data base user and data base
mysql -u root -e "CREATE DATABASE moodle DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
mysql -u root -e "CREATE USER moodleuser@localhost IDENTIFIED BY 'moodleuserpassword'"
mysql -u root -e "GRANT SELECT,INSERT,UPDATE,DELETE,CREATE,CREATE TEMPORARY TABLES,DROP,INDEX,ALTER ON moodle.* TO moodleuser@localhost"

# create config.php
cd /var/www/html/moodle/admin/cli
php install.php --wwwroot="$url/moodle" --dataroot=/opt/moodledata --dbtype=mariadb --dbuser=moodleuser --dbpass=moodleuserpassword --fullname="Test Moodle" --shortname="Test" --adminuser=admin --adminpass=Admin123. --adminemail="admin@no.where" --agree-license --skip-database --non-interactive

# add reverseproxy option to config.php
sed -i "s#'admin';#'admin';\n\$CFG->reverseproxy = true;#g" /var/www/html/moodle/config.php

# move config.php to moodle_data (backuo for container restart)
cp /var/www/html/moodle/config.php /opt/moodledata/config.php

# create tables
cd /var/www/html/moodle/admin/cli
php install_database.php --adminpass=Admin123. --agree-license

# make data base files accessible to all users
# (else, deleting the data base outside the container requires root privileges)
chown -R mysql:mysql /var/lib/mysql
chmod -R a+rwX /var/lib/mysql

# make Moodle files readable for non-root users (www-data!)
chmod -R a+r /var/www/html/moodle

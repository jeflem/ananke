#!/bin/bash

read -p "Domain of your Moodle container (e.g. https://192.168.178.229, no trailing slash!): " domain
read -p "URL path of your Moodle container (e.g. /moodle, will be appended to the domain, no trialing slash!): " path

# write URL path to nginx config
sed -i "s#MOODLE_URL_PATH#$path#g" /etc/nginx/sites-available/default
systemctl restart nginx

# create Moodle data base user and data base
mysql -u root -e "CREATE DATABASE moodle DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
mysql -u root -e "CREATE USER moodleuser@localhost IDENTIFIED BY 'moodleuserpassword'"
mysql -u root -e "GRANT SELECT,INSERT,UPDATE,DELETE,CREATE,CREATE TEMPORARY TABLES,DROP,INDEX,ALTER ON moodle.* TO moodleuser@localhost"

# create config.php
cd /var/www/html/moodle/admin/cli
php install.php --wwwroot="$domain$path" --dataroot=/opt/moodledata --dbtype=mariadb --dbuser=moodleuser --dbpass=moodleuserpassword --fullname="Test Moodle" --shortname="Test" --adminuser=admin --adminpass=Admin123. --adminemail="admin@no.where" --agree-license --skip-database --non-interactive

# add several option to config.php
# - reverse proxy mode
# - router configured
# - SSL proxy mode
# - debug output
# - registerauth (to remove a warning on the login page, seems to be a bug in Moodle that this option is used although undefined)
sed -i "s#'admin';#'admin';\n\$CFG->reverseproxy = true;\n\$CFG->routerconfigured = true;\n\$CFG->sslproxy = true;\n\$CFG->debugdisplay = true;\n\$CFG->debug = E_ALL;\n\$CFG->registerauth = '';#g" /var/www/html/moodle/config.php

# move config.php to moodle_data (backup for container restart)
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

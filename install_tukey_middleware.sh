#!/bin/bash

# Somewhat sloppy but hopefully complete script for installing the 
# tukey middleware.  Meant mostly for thourough documentation.

. install_settings.sh

if $INSTALL_PRE
then
    sudo apt-get update
    sudo apt-get install -y \
    git \
    apache2 \
    libapache2-mod-wsgi \
    python-virtualenv \
    postgresql-9.1 \
    postgresql-server-dev-9.1 \
    postgresql-server-dev-all \
    swig \
    build-essential \
    memcached \
    python-dev \
    euca2ools \
    python-psycopg2
fi

if $CLONE_MIDDLEWARE;
then
	git clone $MIDDLEWARE_REPO $TEMP_DIR
	sudo cp -r $TEMP_DIR $MIDDLEWARE_DIR
	sudo chown -R $TUKEY_USER:$TUKEY_GROUP $MIDDLEWARE_DIR
	cd $MIDDLEWARE_DIR
fi

# Need to symlink this 
ln -s $LOCAL_SETTINGS_FILE $MIDDLEWARE_DIR/local/local_settings.py

cd $MIDDLEWARE_DIR

# the parameters we can pass to this script to prevent it from installing
# the database is:		--no-database
# Dont install the logdir: 	--no-logdir
# No apache:			--no-apache

# do the apache stuff ourself
python tools/install_venv.py --no-apache --no-database

# need to configure these bad boys first 

for site_name in auth glance nova
do
    # replace ${PORTS[$site_name]} and replace tukey_cli
    echo "# Generated by install_tukey_middleware.sh
NameVirtualHost $PROXY_HOST:${PORTS[$site_name]}

<Virtualhost $PROXY_HOST:${PORTS[$site_name]}>

WSGIScriptAlias / $MIDDLEWARE_DIR/${WSGI_DIR[$site_name]}/${site_name}_wsgi.py

WSGIDaemonProcess tukey-$site_name user=$TUKEY_USER group=$TUKEY_GROUP processes=3 threads=1 python-path=$MIDDLEWARE_DIR/local:$MIDDLEWARE_DIR/${WSGI_DIR[$site_name]}:$MIDDLEWARE_DIR/.venv/lib/python2.7/site-packages:$MIDDLEWARE_DIR/.venv/local/lib/python2.7/site-packages

WSGIProcessGroup tukey-$site_name

ErrorLog /var/log/apache2/tukey-${site_name}-error.log
CustomLog /var/log/apache2/tukey-${site_name}-access.log combined

<Directory $MIDDLEWARE_DIR/${WSGI_DIR[$site_name]}>
  Order allow,deny
  Allow from all
</Directory>

</virtualhost>" > $MIDDLEWARE_DIR/bin/${site_name}-apache.conf

    sudo ln -s $MIDDLEWARE_DIR/bin/${site_name}-apache.conf $APACHE_SITES_AVAILABLE/${site_name}
    sudo a2ensite $site_name
done

# Create configuration files from templates
ln -s $CONFIG_GEN_SETTINGS_FILE $MIDDLEWARE_DIR/config_gen/settings.py
python $MIDDLEWARE_DIR/config_gen/config_gen.py $MIDDLEWARE_DIR

# linking pgp public keys 

ln -s $PGP_KEYDIR $MIDDLEWARE_DIR/tukey_cli/etc/keys

echo "Please edit auth_proxy/iptables.py to have proper settings then RUN!!!"

if $CREATE_NEW_INTERFACE
then
    /sbin/ip addr add $PROXY_HOST dev lo
fi

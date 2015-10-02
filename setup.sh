#/usr/bin/env bash

echo "Installing yang-explorer .."
echo "Checking environment .."
command -v pyang >/dev/null 2>&1 || {
	echo "pyang not found.. please install pyang before continuing !!" >&2;
	exit 1;
}

command -v pip >/dev/null 2>&1 || {
	echo "pip not found.. please install python pip before continuing !!" >&2;
	exit 1;
}

command -v virtualenv >/dev/null 2>&1 || {
	echo "virtualenv not found.. please install virtualenv before continuing !!" >&2;
	exit 1;
}

echo "Creating / Activating virtualenv .."
if [ -f "v/bin/activate" ]; then
	source v/bin/activate
else
	virtualenv v
	source v/bin/activate
fi

echo "Installing dependencies .."
pip install -r requirements.txt
rc=$?
if [[ $rc != 0 ]]; then
	echo "Installation failed !! aborted !!"
	exit $rc
fi

echo "Setting up initial database .."

if [ -f "server/data/db.sqlite3" ]; then
	echo "Database already exist .. skipping"
else
	cd server
	echo "Creating data directories .."
	mkdir -p data/users
	mkdir -p data/session
	mkdir -p data/collections

	if [ ! -d "data/users" ]; then
		echo "Failed to create data directories !!"
		echo "Setup failed !!"
		exit -1
	fi

	echo "Creating database .."
	python manage.py migrate
	echo "Creating default users .."
	python manage.py setupdb
	cd ..
fi

if [ -d "server/data/users/guest/yang" ]; then
	echo "Copying default models .."
	cp default-models/* server/data/users/guest/yang/
	cd server
	GUESTPATH=data/users/guest
	DEFAULT_YANG=$GUESTPATH/yang/ietf-interfaces@2013-12-23.yang
	DEFAULT_CXML=$GUESTPATH/cxml/ietf-interfaces@2013-12-23.xml
	pyang --plugindir explorer/plugins -p $GUESTPATH/yang -f cxml  $GUESTPATH/yang/*.yang $DEFAULT_YANG > $DEFAULT_CXML
	cd ..
fi

echo "Setup completed.. "
echo "Use start.sh to start yang-explorer server"

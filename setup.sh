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
    NOVENV=1
    echo ""
    echo "WARNING: virtualenv not found !!"
    echo "Without virtualenv, required python packages will be installed in system python"
    echo "environment and you may require superuser permission."
    echo ""
    printf "Do you want to continue? (y/Y) "
    read response

    if printf "%s\n" "$response" | grep -Eq "$(locale yesexpr)"
    then
        break;
    else
        exit 1;
    fi
}

if [[ $NOVENV != 1 ]]; then
    echo "Creating / Activating virtualenv .."
    if [ -f "v/bin/activate" ]; then
        source v/bin/activate
    else
        virtualenv v
        source v/bin/activate
    fi
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
    if [[ $UID == 0 ]]; then
        echo ""
        echo "Warning: Setting up database as root, this is not recommended."
        echo "Alternatively you can re-run this script as non-root"
        echo "to setup database without root privilege."
        echo ""
        printf "Do you want to continue as root ? (n/N) "
        read response

        if printf "%s\n" "$response" | grep -Eq "$(locale yesexpr)"
            then
            break;
        else
            exit 1;
        fi
    fi

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

add_model() {
	GUESTPATH=data/users/guest
	DEFAULT_YANG=$GUESTPATH/yang/$1.yang
	DEFAULT_CXML=$GUESTPATH/cxml/$1.xml
	pyang --plugindir explorer/plugins -p $GUESTPATH/yang -f cxml  $GUESTPATH/yang/*.yang $DEFAULT_YANG > $DEFAULT_CXML
}

if [ -d "server/data/users/guest/yang" ]; then
    count=$(find server/data/users/guest/yang -maxdepth 1 -type f -name '*.yang' | wc -l)
    if [ $count -eq 0 ] ; then
        echo "Copying default models .."
        cp default-models/* server/data/users/guest/yang/
        cd server
        add_model "ietf-interfaces@2013-12-23"
        add_model "ietf-netconf-monitoring@2010-10-04"
        cd ..
    fi
fi

echo "Setup completed.. "
echo ""
echo "Use start.sh to start yang-explorer server"

#/usr/bin/env bash

show_help() {
    echo 'Usage: bash setup.sh [-y] [-a [<filename>]]'
    echo '       -y [optional] accept default yes to interactive prompt'
    echo '          Setup may require user confirmation when running without'
    echo '          virtualenv or as superuser'
    echo '       -a [<filename>] An annotation file name to install'
    echo '       -r Uninstall annotation file'
}

OPTIND=1
# Initialize our own variables:
default_yes=0
no_db=0
ann_file=''
remove_ann_file=0

while getopts "h?yna:r" opt; do
    case "$opt" in
    h|\?)
        show_help
        exit 0
        ;;

    y)  default_yes=1
        ;;

    n)  no_db=1
        ;;

    a)  ann_file=${OPTARG}
        ;;

    r)  remove_ann_file=1
        ann_file=''
        ;;
    esac
done

shift $((OPTIND-1))
[ "$1" = "--" ] && shift

echo "Installing yang-explorer .."
echo "Checking environment .."

command -v pip >/dev/null 2>&1 || {
	echo "pip not found.. please install python pip before continuing !!" >&2;
	exit -1;
}

command -v virtualenv >/dev/null 2>&1 || {
    NOVENV=1
    echo ""
    echo "WARNING: virtualenv not found !!"
    echo "Without virtualenv, required python packages will be installed in system python"
    echo "environment and you may require superuser permission."
    echo ""
    if [[ $default_yes != 1 ]]; then
        printf "Do you want to continue? (y/Y) "
        read response

        if printf "%s\n" "$response" | grep -Eq "$(locale yesexpr)"
        then
            break;
        else
            exit -1;
        fi
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
        if [[ $default_yes != 1 ]]; then
            printf "Do you want to continue as root ? (n/N) "
            read response

            if printf "%s\n" "$response" | grep -Eq "$(locale yesexpr)"
                then
                break;
            else
                exit 1;
            fi
        fi
    fi

	cd server
	echo "Creating data directories .."
	mkdir -p data/users
	mkdir -p data/session
	mkdir -p data/collections
	mkdir -p data/annotation

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

if [ "$ann_file" != "" ]  && [ -f $ann_file ]; then
	mkdir -p server/data/annotation
    cp $ann_file server/data/annotation/
    echo "Annotation installed at data/annotation"
elif [[ $remove_ann_file != 0 ]]; then
	rm -f server/data/annotation/*.json
    echo "Annotation uninstalled from data/annotation"
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

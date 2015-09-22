#/usr/bin/env bash

echo "Installing yang-explorer .."
echo "Checking environment .."
command -v pyang >/dev/null 2>&1 || {
	echo "pyang not found.. please install pyang before continuing !!" >&2;
	exit 1;
}

command -v pyang >/dev/null 2>&1 || {
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
echo "Setup completed.. "

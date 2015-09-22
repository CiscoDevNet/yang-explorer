#!/usr/bin/env bash

echo ""
echo "Starting YangExplorer server .."
if [ -f "v/bin/activate" ]; then
	echo "Activating virtualenv .."
	source v/bin/activate
fi

HOST='localhost'
PORT='8088'

echo "Use http://$HOST:$PORT/static/YangExplorer.html"
echo ""

cd server
python manage.py runserver $HOST:$PORT

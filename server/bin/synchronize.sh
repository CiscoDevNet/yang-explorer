#!/usr/bin/env bash
#
# Script to Compile Yang into CXML

FILE_NAME=$1
USER_NAME=$2
SESSION_KEY=$3

NAME=`basename $FILE_NAME .yang`
USER_PATH=data/users/$USER_NAME/yang
USER_FILES=""
if [ -d $USER_PATH ]; then
    if find "$USER_PATH" -mindepth 1 -print -quit | grep -q .; then
        USER_FILES="$USER_PATH/*.yang"
    fi
fi

if [ -z $SESSION_KEY ]; then
    CXMLNAME=data/users/$USER_NAME/cxml/$NAME.xml
    SESSION_PATH=''
    SESSION_FILES=''
    INC_PATH="$SESSION_PATH:$USER_PATH"
else        
    CXMLNAME=data/session/$SESSION_KEY/$NAME.xml
    SESSION_PATH=data/session/$SESSION_KEY
    SESSION_FILES=$SESSION_PATH/*.yang
    INC_PATH="$USER_PATH"
fi

echo "pyang --plugindir explorer/plugins -p $INC_PATH -f cxml $SESSION_FILES $USER_FILES $FILE_NAME > $CXMLNAME"
pyang --plugindir explorer/plugins -p $INC_PATH -f cxml $SESSION_FILES $USER_FILES $FILE_NAME > $CXMLNAME

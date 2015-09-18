#!/usr/bin/env bash
#
# Script to Compile Yang into import dependencies

USER_NAME=$1
SESSION_KEY=$2

USER_PATH=data/users/$USER_NAME/yang
USER_FILES=""

if [ -d $USER_PATH ]; then
    if find "$USER_PATH" -mindepth 1 -print -quit | grep -q .; then
        USER_FILES="$USER_PATH/*.yang"
        echo "UserFiles: $USER_FILES"
    else
        echo "No files in the directory !!"
        exit 0
    fi
else
    echo "User directory not found"
    exit 0
fi

echo "$0 $1 $2"

if [ -z "$SESSION_KEY" ]; then
    INC_PATH=$USER_PATH
    OUT_FILE=data/users/$USER_NAME/dependencies.xml
else
    SESSION_PATH=data/session/$SESSION_KEY
    OUT_FILE="$SESSION_PATH/dependencies.xml"
    INC_PATH="$USER_PATH:$SESSION_PATH"
    USER_FILES="$USER_FILES $SESSION_PATH/*.yang"
fi


echo "pyang --plugindir explorer/plugins -p $INC_PATH -f pyimport $USER_FILES > $OUT_FILE"
pyang --plugindir explorer/plugins -p $USER_PATH -f pyimport $USER_FILES > $OUT_FILE



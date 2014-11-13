#!/bin/bash

function emulator_avd() {

    avds=($(for f in `find ~/.android/avd/*.ini -iname *.ini`; do echo `basename $f .ini`; done))
    select avd in ${avds[*]}
    do
        emulator -avd $avd -skindir "$1" -skin "$2" ${*:3}
        break
    done
}

SKINDIR=`dirname "$1"`

# Check for skin name argument
if [ -z "$1" ]; then
    echo 
    echo "USAGE : $0 <skin_name> [emulator_args]"
    echo    
    echo "<skin_name> is a subdirectory in $SKINDIR/"
    exit 1
fi

SKINNAME=`basename "$1"`
SKINPATH=$SKINDIR/$SKINNAME

# Check if skin directory is valid
if ! [ -f "$SKINPATH/layout" ]; then
    echo "emulator: ERROR: could not load skin '$SKINPATH'"
    exit 2
fi

echo
echo Please select AVD to start with skin \"$SKINNAME\" : 
echo

emulator_avd "$SKINDIR" "$SKINNAME" ${*:2}


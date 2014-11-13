#! /bin/sh

if [ -z "$1" ]; then
    echo 
    echo "USAGE : $0 <image.xcf>"
    echo 
    exit 1 
fi

scriptdir=`dirname "$0"`

XCF_FILE=$1 gimp -idf --batch-interpreter=python-fu-eval -b - -b 'pdb.gimp_quit(0)' < $scriptdir/gimp-plugin/gimp_export_skin.py

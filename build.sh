#! /bin/bash -e


pushd `dirname $0` > /dev/null
here=$PWD
popd > /dev/null

python "${here}"/src/concert_branding/logos.py "${here}"/build
cp -a "${here}"/static/* "${here}"/build

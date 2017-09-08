#! /bin/bash -e


pushd `dirname $0` > /dev/null
here=$PWD
popd > /dev/null

python "${here}"/src/logos.py "${here}"/build

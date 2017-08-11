#! /bin/bash -e


pushd `dirname $0` > /dev/null
here=$PWD
popd > /dev/null

docker build --tag concert_branding ${here}/serve
docker run --rm \
    -p 8080:80 \
    -v ${here}/build:/var/www/html \
    -v ${here}/static:/var/www/html/static \
    concert_branding

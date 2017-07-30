#! /bin/bash -e


pushd `dirname $0` > /dev/null
here=$PWD
popd > /dev/null

docker build --tag concert_branding .
docker run --rm -p 8080:80 -v $here:/var/www/html concert_branding

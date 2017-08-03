#! /bin/bash -e


pushd `dirname $0` > /dev/null
here=$PWD
popd > /dev/null

docker build --tag concert_branding ${here}
docker run --rm -p 8080:80 -v $(dirname ${here}):/var/www/html concert_branding

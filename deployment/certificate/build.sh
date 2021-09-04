#!/bin/bash -e

IMAGE="aividtech/smtc_certificate"
DIR=$(dirname $(readlink -f "$0"))

. "$DIR/../../script/build.sh"

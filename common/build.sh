#!/bin/bash -e

IMAGE="aividtech/smtc_common"
DIR=$(dirname $(readlink -f "$0"))
. "$DIR/../script/build.sh"

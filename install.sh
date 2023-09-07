#!/bin/sh

log() {
  echo $(date "+%Y-%m-%d %H:%M:%S") "$@"
}

fail() {
  log $@
  exit 1
}

OT_VERSION_FILE=/etc/VERSION.json
[[ -f ${OT_VERSION_FILE} ]] || fail "${OT_VERSION_FILE} does not exist"

export OT_API_VERSION=`cat "${OT_VERSION_FILE}" | python -c "import sys, json; print(json.load(sys.stdin)['opentrons_api_version'])"`
[[ ${OT_API_VERSION} ]] || fail "opentrons_api_version not specified in ${OT_VERSION_FILE}"

GITHUB_ROOT="https://raw.githubusercontent.com/genie-inc/opentrons_rest_api/master"

wget -q "${GITHUB_ROOT}/server/server.py" -O server.py || fail "Cannot download server.py"
wget -q "${GITHUB_ROOT}/opentrons-rest-server.service" -O opentrons-rest-server.service || fail "Cannot download opentrons-rest-server.service"
chmod 644 server.py opentrons-rest-server.service

# stop the service if it already exists
systemctl stop opentrons-rest-server >/dev/null 2>&1

echo Installing ...
mount -o remount,rw /
mkdir -p /data/user_storage/opentronsrestserver
mv server.py /data/user_storage/opentronsrestserver/
mv opentrons-rest-server.service /etc/systemd/system/
systemctl enable opentrons-rest-server || fail "Cannot enable REST API"
systemctl start opentrons-rest-server || fail "Cannot enable REST API"
echo Successfully installed REST API extension

#!/bin/sh

log() {
  echo $(date "+%Y-%m-%d %H:%M:%S") "$@"
}

fail() {
  log $@
  exit 1
}

OT_VERSION_FILE=/etc/VERSION.json
[ -f ${OT_VERSION_FILE} ] || fail "${OT_VERSION_FILE} does not exist"

OT2_TYPE="OT-2 Standard"
OT3_TYPE="OT-3 Standard"

export OT_ROBOT_TYPE=`cat "${OT_VERSION_FILE}" | python3 -c "import sys, json; print(json.load(sys.stdin)['robot_type'])"`
[ -z "${OT_ROBOT_TYPE}" ] && fail "robot_type not specified in ${OT_VERSION_FILE}"
[ "${OT_ROBOT_TYPE}" == "${OT2_TYPE}" ] || [ "${OT_ROBOT_TYPE}" == "${OT3_TYPE}" ] || fail "Robot type ${OT_ROBOT_TYPE} is not supported"


GITHUB_ROOT="https://raw.githubusercontent.com/genie-inc/opentrons_rest_api/master"

wget -q "${GITHUB_ROOT}/server/server.py" -O server.py || fail "Cannot download server.py"
wget -q "${GITHUB_ROOT}/opentrons-rest-server.service" -O opentrons-rest-server.service || fail "Cannot download opentrons-rest-server.service"
chmod 644 server.py opentrons-rest-server.service

# do not set the PYTHONPATH on OT-2 robots
[ "${OT_ROBOT_TYPE}" == "${OT2_TYPE}" ] && sed -i '/PYTHONPATH/d' opentrons-rest-server.service

# stop the service if it already exists
systemctl stop opentrons-rest-server >/dev/null 2>&1
systemctl disable opentrons-rest-server >/dev/null 2>&1

echo Installing ...
mount -o remount,rw /
mkdir -p /data/user_storage/opentronsrestserver
mv server.py /data/user_storage/opentronsrestserver/
mv opentrons-rest-server.service /etc/systemd/system/
systemctl enable opentrons-rest-server || fail "Failed to enable REST API Service"
systemctl start opentrons-rest-server || fail "Failed to start REST API Service"
echo Successfully installed REST API extension

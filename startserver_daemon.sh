#!/usr/bin/env bash
function log(){
	logger -i -t sync $1
	echo $1
}

start(){
OUT_FILE=/tmp/iot-nohup.out
#mv -f -v $OUT_FILE $OUT_FILE.last
#$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
log "Current dir for haiot daemon is $DIR"
$DIR/startserver.sh db_mem model_auto_update syslog=logs2.papertrailapp.com:30445 live $1 $2 $3 $4 $5  2>&1 | logger -i -t sync
log "Haiot startserver daemon exit" >> $OUT_FILE
}

stop() {
	me=`basename $0`
        log "Stopping script $me"
        $DIR/scripts/stopserver.sh
}

log "Executing script with parameter $1 $2 $3"
DIR="$(dirname "$(readlink -f "$0")")"
if [ "$1" = "stop" ]; then
        stop
else
        start
fi


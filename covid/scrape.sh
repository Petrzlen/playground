#!/bin/bash

function alert {
	# Using alias to de-dupe. Proud of myself to think of it before being flooded from alerts.
	curl -X POST "https://api.opsgenie.com/v2/alerts" -H "Content-Type: application/json" -H "Authorization: GenieKey $GENIE_KEY" -d '{"message": "Appointment ready!", "description": "Check the site", "alias": "'$1'"}'
}

for i in `seq 10000`; do
	F="data/`date +'%s'`.json"
	echo $F
	curl -s "https://home.color.com/api/v1/sample_collection_appointments/availability?claim_token=3c152022ec5d6b1ab1e152b63a0c9b12fae0&collection_site=Embarcadero" | jq . > $F
	grep start $F | sort | head -4
#	if grep -q "2020-07-0[6-8]" $F; then
#		echo "Might get lucky!"
#		alert "covid-maybe"
#	fi;
	if grep -q "\(2020-07-06T[12]\|2020-07-07\|2020-07-08T1\)" $F; then
		echo "Jackpot"
		alert "covid-jackpot"
	fi;
	
	sleep 10  # wonder how many of the competing scripts are doing this
done

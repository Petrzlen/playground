#/bin/bash

echo $GENIE_KEY
curl -X POST "https://api.opsgenie.com/v2/alerts" \
    -H "Content-Type: application/json" \
    -H "Authorization: GenieKey $GENIE_KEY" \ 
    -d '{"message": "Appointment ready!", "description": "Check the site"}'


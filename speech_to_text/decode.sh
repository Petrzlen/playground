export GOOGLE_APPLICATION_CREDENTIALS="/Users/peter/speech_to_text/key.json"
URL="https://ia800501.us.archive.org/28/items/Item291HowToHangLaundry/OMHT291.mp3"
set -x

curl -X POST \
     -H "Authorization: Bearer "$(gcloud auth application-default print-access-token) \
     -H "Content-Type: application/json; charset=utf-8" \
     --data "{
  'config': {
    'language_code': 'en-US'
  },
  'audio':{
    'uri':'$URL'
  }
}" "https://speech.googleapis.com/v1/speech:longrunningrecognize"

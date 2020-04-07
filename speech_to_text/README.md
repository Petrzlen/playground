```
https://audio.online-convert.com/convert-to-flac  (mono)

speech_to_text$ gsutil cp ~/Downloads/typek*  gs://furt-sa-daco/

speech_to_text$ gcloud ml speech operations describe 2483865980747838513
{
  "metadata": {
    "@type": "type.googleapis.com/google.cloud.speech.v1.LongRunningRecognizeMetadata",
    "lastUpdateTime": "2019-08-27T08:30:52.142476Z",
    "progressPercent": 25,
    "startTime": "2019-08-27T08:29:35.721524Z"
  },
  "name": "2483865980747838513"
}
speech_to_text$ gcloud ml speech recognize-long-running gs://furt-sa-daco/typek2.flac --language-code='en-US' --async
Check operation [operations/8369156479442332829] for status.
{
  "name": "8369156479442332829"
}

2483865980747838513 8369156479442332829 3016634945857632240
```

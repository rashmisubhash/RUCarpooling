import json
import requests
import base64
import os

def lambda_handler(event, context):
    # Groq API endpoint
    url = 'https://api.groq.com/openai/v1/audio/transcriptions'
    
    # Your Groq API Key
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    try:
        # Load the event body and extract the audio file
        body = json.loads(event['body'])
        audio_base64 = body.get('audio_file')  # base64 encoded audio file
        audio_filename = body.get('filename', 'audio_file.wav')

        # Check if audio_file is provided and is a non-empty string
        if not audio_base64:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No audio file provided'})
            }

        # Decode the base64 audio file using the base64 module
        try:
            audio_data = base64.b64decode(audio_base64)
        except Exception as decode_error:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Error decoding base64 audio: {str(decode_error)}'})
            }

        # Specify the model for transcription
        model = "whisper-large-v3-turbo"  # Groq's model for speech-to-text (use the correct model name if needed)

        # Send the audio to Groq API for transcription
        headers = {'Authorization': f'Bearer {GROQ_API_KEY}'}
        files = {'file': (audio_filename, audio_data, 'audio/wav')}
        payload = {'model': model}  # Include model field in the request

        # Make the request
        response = requests.post(url, headers=headers, files=files, data=payload)

        # Check if the request was successful
        if response.status_code == 200:
            transcribed_text = response.json().get('text', '')
            return {
                'statusCode': 200,
                'body': json.dumps({'transcribed_text': transcribed_text})
            }
        else:
            return {
                'statusCode': response.status_code,
                'body': json.dumps({'error': 'Transcription failed', 'details': response.text})
            }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f"Internal error: {str(e)}"})
        }



# zip function.zip groq_speech_to_text.py
# aws lambda update-function-code \
#     --function-name RUGroqSpeechText \
#     --zip-file fileb://function.zip \
#     --region us-east-1
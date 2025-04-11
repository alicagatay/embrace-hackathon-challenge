from openai import AzureOpenAI
import whisper

import azure.cognitiveservices.speech as speechsdk

import pyttsx3
from gtts import gTTS

# model = whisper.load_model("base")
# result = model.transcribe("Test/1.mp3")
# print("user:",result["text"])


# Configuration
import tomli
import os

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from pydub import AudioSegment
import os

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

try:  
    with open("config.toml", "rb") as f:
        toml_dict = tomli.load(f)

    ENDPOINT = toml_dict["configs"]["ENDPOINT"]
    AZURE_API_KEY = toml_dict["configs"]["AZURE_API_KEY"]
    AZURE_SPEECH_KEY = toml_dict["configs"]["AZURE_SPEECH_KEY"]
    AZURE_REGION = toml_dict["configs"]["AZURE_REGION"]
    API_VERSION = toml_dict["configs"]["API_VERSION"]
    MODEL_NAME = toml_dict["configs"]["MODEL_NAME"]

except:
    pass

client = AzureOpenAI(
    azure_endpoint=ENDPOINT,
    api_key=AZURE_API_KEY,
    api_version=API_VERSION,
)


# def turn_text_to_voice(response_text,output_path):
#     engine = pyttsx3.init()

#     voices = engine.getProperty('voices')

#     # Set the desired voice (e.g., choosing the second voice)
#     engine.setProperty('voice', voices[1].id)  # Change the index as needed

#     # Optionally, change rate (speed of speech)
#     engine.setProperty('rate', 150)  # Default is 200, lower values make the speech slower

#     # Optionally, change volume (range from 0.0 to 1.0)
#     engine.setProperty('volume', 1.0)  # Full volume

#     #engine.say(response_text)
#     engine.save_to_file(response_text, output_path)
#     engine.runAndWait()

def turn_text_to_voice(response_text, output_path):
    tts = gTTS(text=response_text, lang='en')
    tts.save(output_path)
    
#-------------------------------------------
#def turn_text_to_voice(response_text):
    # speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    # speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"  # You can change the voice

    # speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

    # # Synthesize and play audio
    # result = speech_synthesizer.speak_text_async(response_text).get()

    # # Check for errors
    # if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
    #     print("Speech synthesized to speaker successfully.")
    # elif result.reason == speechsdk.ResultReason.Canceled:
    #     cancellation = result.cancellation_details
    #     print("Speech synthesis canceled: {}".format(cancellation.reason))
    #     if cancellation.reason == speechsdk.CancellationReason.Error:
    #         print("Error details: {}".format(cancellation.error_details))

#------------------------------------------
# audio_config = speechsdk.audio.AudioOutputConfig(filename="output.wav")
# speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
# speech_synthesizer.speak_text_async(response_text).get()


@app.post("/upload-audio/")
async def upload_audio(file: UploadFile = File(...)):
    # Save the received file
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())

    # Load the audio file using pydub (it will automatically detect the format)
    audio = AudioSegment.from_file(file_location)

    # Set the output file path for MP3 format
    temp_file = os.path.join(UPLOAD_DIR, "temp_audio.mp3")
    output_file = os.path.join(UPLOAD_DIR, "output_audio.mp3")

    # Convert the audio to MP3 format
    audio.export(temp_file, format="mp3")

    model = whisper.load_model("base")
    result = model.transcribe(temp_file)
    print("user:",result["text"])

    MESSAGES = [
    #{"role": "system", "content": "You are a doctor's assistant. Be kind, patient, gentle, friendly, and understanding. Speak with empathy, act delicately, and approach situations with calm logic."},
    {"role": "system", "content": "You are a doctor's assistant. Be kind, patient, gentle, friendly, and understanding. Speak with empathy, act delicately, and approach situations with calm logic."},
    {"role": "user", "content": result["text"]},
]

    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=MESSAGES,
        max_tokens=100,
    )

    #print(completion.model_dump_json(indent=2))
    response_text = completion.choices[0].message.content
    print("\nAssistant:",response_text)

    turn_text_to_voice(response_text,output_file)

    # Return the converted audio file as response
    return FileResponse(output_file, media_type="audio/mp3")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
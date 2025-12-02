import os
from groq import Groq

GROQ_API_KEY   = os.environ.get("GROQ_API_KEY")
ASR_MODEL      = "whisper-large-v3-turbo"

groq_client = Groq(api_key=GROQ_API_KEY)
filename = "/home/brad/voice/output.wav"
print(GROQ_API_KEY)

# Open the audio file
with open(filename, "rb") as file:
    # Create a transcription of the audio file
    transcription = groq_client.audio.transcriptions.create(
      file=file, # Required audio file
      model="whisper-large-v3-turbo", # Required model to use for transcription
    #   prompt="Specify context or spelling",  # Optional
    #   response_format="verbose_json",  # Optional
    #   timestamp_granularities = ["word", "segment"], # Optional (must set response_format to "json" to use and can specify "word", "segment" (default), or both)
    #   language="en",  # Optional
    #   temperature=0.0  # Optional
    )
    # To print only the transcription text, you'd use print(transcription.text) (here we're printing the entire transcription object to access timestamps)
    print(json.dumps(transcription, indent=2, default=str))
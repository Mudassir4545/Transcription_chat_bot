import os
import json
from flask import Flask, jsonify, request, send_file, send_from_directory
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import assemblyai as aai
import mimetypes
from dotenv import load_dotenv


mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')

load_dotenv()

# Initialize the Flask app
app = Flask(__name__)

# Get API keys from environment variables
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Set AssemblyAI API key
aai.settings.api_key = ASSEMBLYAI_API_KEY

# Set Google API key for Gemini model
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# Define a directory to save uploaded audio files
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Refined Instructions for Gemini
GEMINI_INSTRUCTIONS = """
The purpose of the category 'Reason for Outbound Call' is to identify the reason that a connected call was placed by the caller.

Consider the following options and select the one that best matches the content of the call:
1. Yes: The agent attempted to discuss buying, selling, trading, leasing, or test driving a vehicle. This includes any discussion of vehicle needs, interests, or potential sales, but this only applies if the call was live.
2. No: The agent followed up on a previous purchase or had a general discussion. This option should be selected if the call does not include any sales-related discussion.
3. No: The agent only confirmed, changed, or canceled an existing appointment. This includes any mention of scheduling, rescheduling, confirming, or canceling appointments.
4. Correction: The call was not connected to the intended party (e.g., it was a voicemail or a one-sided message).

Remember:
- Option 1 should only be selected if there was a live conversation with the intended contact.
- Option 4 should be selected if the call was not connected (e.g., it was a voicemail or no live interaction occurred).
- Option 4 it is voice mail, make it option 4 
"""

# Home route to serve the index.html file
@app.route('/')
def home():
    return send_file('web/index.html')

# API route to handle file upload, transcription, and model interaction
@app.route("/api/upload", methods=["POST"])
def generate_api():
    if request.method == "POST":
        try:
            # Check if an audio file was uploaded
            if 'audio_file' not in request.files:
                return jsonify({"error": "No audio file provided"}), 400

            audio_file = request.files['audio_file']
            if audio_file.filename == '':
                return jsonify({"error": "No selected file"}), 400

            # Save the uploaded file to the server
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_file.filename)
            audio_file.save(file_path)

            # Transcribe the audio using AssemblyAI
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(file_path)

            # Send transcription and instructions to Gemini model
            model = ChatGoogleGenerativeAI(model="gemini-pro")
            message = HumanMessage(content=f"{GEMINI_INSTRUCTIONS}\n\nCall Transcription: {transcript.text}")
            response = model.stream([message])

            # Interpret the model's response to select the correct option
            buffer = []
            for chunk in response:
                buffer.append(chunk.content)

            result_text = ''.join(buffer).lower()

            # Adjusted logic to determine the correct option
            if ("option 4" in result_text or "voicemail" in result_text or 
                "just wanted to reach out" in result_text or "thank you, bye" in result_text or 
                "this is" in result_text and "see if" in result_text and not "response" in result_text):
                selected_option = 4
            elif "option 1" in result_text or "yes" in result_text or "vehicle needs" in result_text:
                selected_option = 1
            elif "option 2" in result_text:
                selected_option = 2
            elif "option 3" in result_text or "reschedule" in result_text or "confirm" in result_text or "cancel" in result_text:
                selected_option = 3
            else:
                selected_option = "Could not determine the correct option."

            # Return the transcription and selected option
            return jsonify({
                "transcription": transcript.text,
                "selected_option": selected_option
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)})

# Route to serve static files
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('web', path)

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, request, render_template, send_from_directory, url_for
import os
import PyPDF2
from gtts import gTTS
from moviepy.editor import TextClip, AudioFileClip, CompositeVideoClip

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'static'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    video_url = None
    if request.method == 'POST':
        file = request.files['file']
        filename = file.filename
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Extract text
        if filename.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file_path)
            text = ''.join([page.extract_text() for page in reader.pages])
        elif filename.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            return "Unsupported file type. Please upload .txt or .pdf."

        # Limit text length for simplicity
        text = text.strip().replace('\n', ' ')
        if len(text) > 500:
            text = text[:500] + '...'

        # Generate audio
        audio_path = os.path.join(OUTPUT_FOLDER, 'output.mp3')
        tts = gTTS(text)
        tts.save(audio_path)

        # Create video
        video_path = os.path.join(OUTPUT_FOLDER, 'output.mp4')
        clip = TextClip(text, fontsize=40, color='white', size=(1280, 720), bg_color='black', duration=15)
        audio = AudioFileClip(audio_path)
        clip = clip.set_audio(audio)
        clip.write_videofile(video_path, fps=24)

        video_url = url_for('static', filename='output.mp4')

    return render_template('index.html', video_url=video_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

from flask import Flask, request, render_template, send_file, redirect, url_for, flash
import os
import pyttsx3
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from PyPDF2 import PdfReader

app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text = request.form.get('input_text', '').strip()
        file = request.files.get('file')

        if not text and not file:
            flash('Please enter text or upload a file.')
            return redirect(url_for('index'))

        if file and file.filename != '':
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            
            if file.filename.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            elif file.filename.endswith('.pdf'):
                reader = PdfReader(file_path)
                text = ''
                for page in reader.pages:
                    text += page.extract_text()
            else:
                flash('Unsupported file type. Please upload .txt or .pdf.')
                os.remove(file_path)
                return redirect(url_for('index'))

            os.remove(file_path)

        # Save audio
        audio_path = os.path.join(OUTPUT_FOLDER, 'output.mp3')
        engine = pyttsx3.init()
        engine.save_to_file(text, audio_path)
        engine.runAndWait()

        # Create video (simple static image + audio)
        image_path = 'background.jpg'  # Provide a default image in your project folder
        video_path = os.path.join(OUTPUT_FOLDER, 'output.mp4')

        audioclip = AudioFileClip(audio_path)
        imageclip = ImageClip(image_path, duration=audioclip.duration)
        imageclip = imageclip.set_audio(audioclip)

        imageclip.write_videofile(video_path, fps=24)

        return redirect(url_for('download'))

    return render_template('index.html')

@app.route('/download')
def download():
    video_path = os.path.join(OUTPUT_FOLDER, 'output.mp4')
    if os.path.exists(video_path):
        return send_file(video_path, as_attachment=True)
    else:
        flash('Video not found. Please generate it first.')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

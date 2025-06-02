from flask import Flask, request, render_template, url_for
import os
import threading
import uuid
import PyPDF2
from gtts import gTTS
from moviepy.editor import VideoFileClip, ImageClip, TextClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, CompositeAudioClip

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'static'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

BACKGROUND_VIDEO = os.path.join(OUTPUT_FOLDER, 'background.mp4')
BACKGROUND_IMAGE = os.path.join(OUTPUT_FOLDER, 'background.jpg')
BACKGROUND_MUSIC = os.path.join(OUTPUT_FOLDER, 'bg_music.mp3')

def split_text(text, max_chars=1000):
    words = text.split()
    chunks, chunk = [], ''
    for word in words:
        if len(chunk) + len(word) + 1 <= max_chars:
            chunk += ' ' + word
        else:
            chunks.append(chunk.strip())
            chunk = word
    if chunk:
        chunks.append(chunk.strip())
    return chunks

def generate_video(text, video_filename):
    chunks = split_text(text)
    video_clips = []

    for idx, chunk in enumerate(chunks):
        audio_path = os.path.join(OUTPUT_FOLDER, f'audio_{idx}.mp3')
        tts = gTTS(chunk)
        tts.save(audio_path)
        audio_clip = AudioFileClip(audio_path)

        duration = audio_clip.duration + 1

        if os.path.exists(BACKGROUND_VIDEO):
            bg_clip = VideoFileClip(BACKGROUND_VIDEO).subclip(0, duration).resize((1280, 720))
        elif os.path.exists(BACKGROUND_IMAGE):
            bg_clip = ImageClip(BACKGROUND_IMAGE, duration=duration).resize((1280, 720))
        else:
            bg_clip = TextClip("", size=(1280, 720), color='black', duration=duration)

        text_clip = TextClip(chunk, fontsize=40, color='white', bg_color='transparent', size=(1200, None)).set_duration(duration).set_position('center')
        composed = CompositeVideoClip([bg_clip, text_clip]).set_audio(audio_clip)

        video_clips.append(composed)

    final_video = concatenate_videoclips(video_clips, method='compose')

    if os.path.exists(BACKGROUND_MUSIC):
        bg_music = AudioFileClip(BACKGROUND_MUSIC).volumex(0.3)
        final_audio = CompositeAudioClip([final_video.audio.volumex(1.0), bg_music.set_duration(final_video.duration)])
        final_video = final_video.set_audio(final_audio)

    final_video_path = os.path.join(OUTPUT_FOLDER, video_filename)
    final_video.write_videofile(final_video_path, fps=24)

@app.route('/', methods=['GET', 'POST'])
def index():
    video_url = None
    if request.method == 'POST':
        input_text = request.form.get('input_text')
        text = ''

        if input_text and input_text.strip():
            text = input_text.strip()
        else:
            file = request.files['file']
            if file and file.filename != '':
                filename = file.filename
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)

                if filename.endswith('.pdf'):
                    reader = PyPDF2.PdfReader(file_path)
                    text = ''.join([page.extract_text() for page in reader.pages])
                elif filename.endswith('.txt'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                else:
                    return "Unsupported file type."

            else:
                return "Please provide text input or upload a file."

        text = text.replace('\n', ' ')
        video_filename = f'output_{uuid.uuid4().hex}.mp4'

        thread = threading.Thread(target=generate_video, args=(text, video_filename))
        thread.start()

        video_url = url_for('static', filename=video_filename)

    return render_template('index.html', video_url=video_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

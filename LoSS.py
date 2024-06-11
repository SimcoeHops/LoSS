import whisper
import os
import asyncio
import aiohttp
import subprocess
import sys
import shutil
import platform
import urllib.request
import zipfile
import argparse

# Load the Whisper model once
model = whisper.load_model("base")

# Check if yt-dlp is installed, if not install it
def check_install_yt_dlp():
    try:
        subprocess.run(["yt-dlp", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (subprocess.CalledProcessError, FileNotFoundError):
        subprocess.run([sys.executable, "-m", "pip", "install", "yt-dlp"], check=True)

# Check if ffmpeg is installed, if not download and install it
def check_install_ffmpeg():
    ffmpeg_installed = shutil.which("ffmpeg") is not None
    if not ffmpeg_installed:
        print("ffmpeg not found, downloading...")
        if platform.system() == "Windows":
            url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
            zip_path = "ffmpeg.zip"
            urllib.request.urlretrieve(url, zip_path)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall("ffmpeg")
            os.remove(zip_path)
            bin_path = find_ffmpeg_bin_path("ffmpeg")
            if bin_path:
                shutil.copy(os.path.join(bin_path, "ffmpeg.exe"), os.getcwd())
                shutil.copy(os.path.join(bin_path, "ffplay.exe"), os.getcwd())
                shutil.copy(os.path.join(bin_path, "ffprobe.exe"), os.getcwd())
            else:
                raise FileNotFoundError("ffmpeg binaries not found after extraction.")
        elif platform.system() == "Linux":
            subprocess.run(["sudo", "apt-get", "install", "-y", "ffmpeg"], check=True)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["brew", "install", "ffmpeg"], check=True)
        else:
            raise Exception("Unsupported OS for automatic ffmpeg installation")
        print("ffmpeg installed")

def find_ffmpeg_bin_path(root_dir):
    for root, dirs, files in os.walk(root_dir):
        if "ffmpeg.exe" in files:
            return root
    return None

# Asynchronous function to call the OpenAI API for summarization
async def async_summarize_text(api_key, text, session, semaphore=None):
    async with semaphore:
        try:
            async with session.post(
                'https://api.openai.com/v1/chat/completions',
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": ("You will be provided with a text transcript from an audio or video "
                                                       "recording of a meeting, discussion, or conversation. Your task is to "
                                                       "carefully review the transcript and produce thorough, well-organized "
                                                       "meeting notes that capture all the essential details, key points, "
                                                       "and relevant information discussed.\n\n"
                                                       "Your output should include:\n\n"
                                                       "1. A concise yet informative summary paragraph that encapsulates the key points and overall purpose of the transcript.\n\n"
                                                       "2. Sections to organize the main topics, themes, or discussions covered in the transcript. Each section should have a descriptive heading and include relevant details, quotes, or examples from the text.\n\n"
                                                       "3. Identification of any stakeholders, organizations, or entities mentioned in the transcript, along with their roles or significance.\n\n"
                                                       "4. A concluding paragraph that ties together the various sections and highlights the overarching message or implications of the transcript.\n\n"
                                                       "Your summary should be thoughtfully structured, coherent, and easy to follow. Organize the information logically, and use clear language to convey the essential points. "
                                                       "Aim to provide a comprehensive yet concise overview that captures the essence of the transcript while preserving its nuances and context.\n\n"
                                                       "Please let me know if you need any clarification or additional guidance before proceeding.")},
                        {"role": "user", "content": text}
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.6
                },
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                response_data = await response.json()
                if 'choices' in response_data:
                    return response_data['choices'][0]['message']['content'].strip()
                else:
                    print(f"Unexpected response structure: {response_data}")
                    return ""
        except Exception as e:
            print(f"Error summarizing text: {e}")
            return ""

# Asynchronous function to generate a unique filename
async def generate_unique_filename(api_key, session, semaphore=None):
    async with semaphore:
        try:
            async with session.post(
                'https://api.openai.com/v1/chat/completions',
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": "Generate a random four-word phrase for a filename, with words separated by underscores."},
                        {"role": "user", "content": "Please generate a random four-word phrase for a filename."}
                    ],
                    "max_tokens": 10,
                    "temperature": 0.9
                },
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                response_data = await response.json()
                if 'choices' in response_data:
                    filename = response_data['choices'][0]['message']['content'].strip().replace(" ", "_")
                    return filename
                else:
                    print(f"Unexpected response structure: {response_data}")
                    return "default_filename"
        except Exception as e:
            print(f"Error generating filename: {e}")
            return "default_filename"

# Transcribe the audio using Whisper model
def transcribe_audio(audio_path):
    result = model.transcribe(audio_path)
    return result["text"]

# Download audio from YouTube using yt-dlp
def download_youtube_audio(youtube_url):
    command = ['yt-dlp', '-f', 'm4a', '--output', 'input/youtube_audio.m4a', youtube_url]
    subprocess.run(command, check=True)
    return "input/youtube_audio.m4a"

# Convert video file to audio using ffmpeg
def convert_video_to_audio(video_file):
    audio_file = "input/video_audio.mp3"
    command = ['ffmpeg', '-i', video_file, '-q:a', '0', '-map', 'a', audio_file]
    subprocess.run(command, check=True)
    return audio_file

# Main function to orchestrate the processing
async def main(api_key):
    # Check and install yt-dlp and ffmpeg if necessary
    check_install_yt_dlp()
    check_install_ffmpeg()

    print("Choose an option:")
    print("1: Transcribe and Summarize YouTube")
    print("2: Transcribe and Summarize Video (other)")
    print("3: Transcribe and Summarize Audio")
    print("4: Summarize Text")
    choice = input("Enter the number of your choice: ")

    audio_file = None
    text_file = None

    if choice == '1':
        youtube_url = input("Enter the YouTube URL: ")
        audio_file = download_youtube_audio(youtube_url)
    elif choice == '2':
        for file in os.listdir('input'):
            if file.endswith(".mp4") or file.endswith(".mkv") or file.endswith(".avi"):
                audio_file = convert_video_to_audio(os.path.join("input", file))
                break
    elif choice == '3':
        for file in os.listdir('input'):
            if file.endswith(".mp3") or file.endswith(".wav") or file.endswith(".m4a"):
                audio_file = os.path.join("input", file)
                break
    elif choice == '4':
        for file in os.listdir('input'):
            if file.endswith(".txt"):
                text_file = os.path.join("input", file)
                break
    else:
        print("Invalid choice. Exiting.")
        return

    if audio_file:
        print(f"Transcribing audio file: {audio_file}")
        transcript = transcribe_audio(audio_file)
        transcript_file = os.path.join("output", "transcript.txt")
        with open(transcript_file, "w", encoding="utf-8") as f:
            f.write(transcript)
        text_file = transcript_file

    if text_file:
        print(f"Reading text file: {text_file}")
        with open(text_file, 'r', encoding='utf-8') as f:
            transcript = f.read()
    else:
        print("No audio or text file found in the directory.")
        return

    # Summarize the transcript
    semaphore = asyncio.Semaphore(5)
    async with aiohttp.ClientSession() as session:
        summary = await async_summarize_text(api_key, transcript, session, semaphore)
        filename = await generate_unique_filename(api_key, session, semaphore)

    # Save the summary with a unique filename
    if summary:
        with open(os.path.join("output", f"{filename}.txt"), "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"Summary saved to output/{filename}.txt")
    else:
        print("Failed to generate a summary.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LoSS - Lots of Stuff Summarizer")
    parser.add_argument("--api-key", required=True, help="Your OpenAI API key")
    args = parser.parse_args()
    
    asyncio.run(main(args.api_key))

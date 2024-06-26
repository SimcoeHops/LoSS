import json
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
import tempfile
import random

# Load the Whisper model once
model = whisper.load_model("medium")

# Function to load system prompts from a JSON file
def load_prompts(json_path="promptpicker.json"):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data["prompts"]

# Function to select a prompt
def select_prompt(prompts):
    print("Available System Prompts:")
    for idx, prompt in enumerate(prompts):
        print(f"{idx + 1}: {prompt['title']}")
    choice = int(input("Enter the number of your choice: "))
    return prompts[choice - 1]["prompt"]

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
async def async_summarize_text(api_key, text, prompt, session, semaphore=None):
    async with semaphore:
        try:
            async with session.post(
                'https://api.openai.com/v1/chat/completions',
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": text}
                    ],
                    "max_tokens": 4000,  # Set this to a safe value below the limit
                    "temperature": 0.7
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

def download_youtube_audio(youtube_url, random_number):
    # Construct the output filename with the random number
    output_filename = f"input/youtube_audio_{random_number}.m4a"
    command = ['yt-dlp', '-f', 'm4a', '--output', output_filename, youtube_url]
    subprocess.run(command, check=True)
    return output_filename

# Convert video file to audio using ffmpeg
def convert_video_to_audio(video_file, random_number):
    audio_file = f"input/video_audio_{random_number}.mp3"
    command = ['ffmpeg', '-i', video_file, '-q:a', '0', '-map', 'a', audio_file]
    subprocess.run(command, check=True)
    return audio_file

def split_text_into_chunks_to_files(text, chunk_size=1500, overlap=50):
    tokens = text.split()
    chunk_files = []
    start = 0
    while start < len(tokens):
        end = start + chunk_size
        chunk = " ".join(tokens[start:end])
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w+', encoding='utf-8')
        temp_file.write(chunk)
        temp_file.close()
        chunk_files.append(temp_file.name)
        start += chunk_size - overlap
    return chunk_files

async def summarize_chunk_files(api_key, chunk_files, prompt):
    summaries = []
    semaphore = asyncio.Semaphore(5)
    async with aiohttp.ClientSession() as session:
        for file_path in chunk_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                chunk = f.read()
            summary = await async_summarize_text(api_key, chunk, prompt, session, semaphore)
            summaries.append(summary)
    return summaries

async def hierarchical_summarize(api_key, text, prompt):
    # Step 1: Initial chunking to files and summarization
    chunk_files = split_text_into_chunks_to_files(text)
    first_level_summaries = await summarize_chunk_files(api_key, chunk_files, prompt)
    
    # Clean up temporary files
    for file_path in chunk_files:
        os.remove(file_path)
    
    # Step 2: Combine summaries
    combined_summary = " ".join(first_level_summaries)
    
    # Step 3: Check if combined summary exceeds token limit
    if len(combined_summary.split()) > 3000:  # Adjust this limit accordingly
        combined_chunk_files = split_text_into_chunks_to_files(combined_summary)
        final_summary = await summarize_chunk_files(api_key, combined_chunk_files, prompt)
        
        # Clean up temporary files
        for file_path in combined_chunk_files:
            os.remove(file_path)
        
        return " ".join(final_summary)
    else:
        return combined_summary

# Main function to orchestrate the processing
async def main(api_key):
    # Load system prompts
    prompts = load_prompts()
    # Select a prompt
    selected_prompt = select_prompt(prompts)

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
    random_number = random.randint(1000, 9999)

    if choice == '1':
        youtube_url = input("Enter the YouTube URL: ")
        audio_file = download_youtube_audio(youtube_url, random_number)
    elif choice == '2':
        for file in os.listdir('input'):
            if file.endswith(".mp4") or file.endswith(".mkv") or file.endswith(".avi"):
                audio_file = convert_video_to_audio(os.path.join("input", file), random_number)
                break
    elif choice == '3':
        for file in os.listdir('input'):
            if file.endswith(".mp3") or file.endswith(".wav") or file.endswith(".m4a"):
                audio_file = os.path.join('input', file)
                break
    elif choice == '4':
        for file in os.listdir('input'):
            if file.endswith(".txt"):
                text_file = os.path.join('input', file)
                break
    else:
        print("Invalid choice. Exiting.")
        return

    if audio_file:
        print(f"Transcribing audio file: {audio_file}")
        transcript = transcribe_audio(audio_file)
        transcript_file = os.path.join("output", f"transcript_{random_number}.txt")
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

    # Save the transcript and ask for user confirmation before summarizing
    with open(os.path.join("output", f"transcript_{random_number}.txt"), "w", encoding="utf-8") as f:
        f.write(transcript)
    print(f"Transcript saved to output/transcript_{random_number}.txt")
    
    # Ask user if they want to summarize the transcript
    summarize_choice = input("Do you want to summarize the transcript? (y/n): ").strip().lower()
    if summarize_choice != 'y':
        print("Skipping summarization.")
        return

    # Summarize the transcript using hierarchical summarization
    semaphore = asyncio.Semaphore(5)
    async with aiohttp.ClientSession() as session:
        summary = await hierarchical_summarize(api_key, transcript, selected_prompt)
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

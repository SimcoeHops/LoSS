# LoSS - Lots of Stuff Summarizer 📜

Welcome to **LoSS** (Lots of Stuff Summarizer)! 

## What Does This Script Do? 🤔

LoSS is a crude Python script designed to create and/or digest a wall of text, create a transcript using OpenAI's Whisper model, and send it to the OpenAI API using GPT 3.5 Turbo (by default, but feel free to change it to GPT4o if you've got deep pockets) in order to create an AI summary. Make sure you pip install requirements.txt, as this script depends on a few python libraries as well as ffmpeg and yt-dlp.

Once you've downloaded the repository, you can run LoSS.py and you'll be presented with 4 options:

1: Transcribe and Summarize YouTube
2: Transcribe and Summarize Video (other)
3: Transcribe and Summarize Audio
4: Summarize Text

If you want to process a YouTube video, you'll select option 1 and you'll be asked for the URL. If you choose options 2 through 4, observe that the folder containing LoSS.py also contains an **input** folder and an **output** folder. If you want to use options 2 through 4 to transcribe and summarize a video file or an audio file, or want a summary of a text file, place it in the **input** folder. When the summary is complete, it will appear in the **output** folder.



## Setup Instructions

### Step 1: Ensure Git is installed
If Git is not already installed, download and install it from [here](https://git-scm.com/downloads). Verify the installation by running the following command in your terminal or command prompt:

```sh
git --version
```

### Step 2: Ensure Python is installed
Download and install Python from [here](https://www.python.org/downloads/). Verify the installation by running the following command:

```sh
python --version
```

### Step 3: Clone the repository
Clone the repository from GitHub using the following command:

```sh
git clone https://github.com/SimcoeHops/LoSS.git
cd LoSS
```

### Step 4: Set up a virtual environment (optional but recommended)
Create and activate a virtual environment:

For Windows:
```sh
python -m venv venv
venv\scripts\activate
```

For MacOS/Linux:
```sh
python -m venv venv
source venv/bin/activate
```

### Step 5: Install required packages
Install the necessary packages from the `requirements.txt` file:

```sh
pip install -r requirements.txt
```

### Step 6: Execute the Python script
Run the Python script with your API key:

```sh
python LoSS.py --api-key YOUR_API_KEY_HERE
```

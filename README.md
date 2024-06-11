# LoSS - Lots of Stuff Summarizer 📜✨

Welcome to **LoSS** (Lots of Stuff Summarizer)! 

So, what's LoSS? Well, that's a fantastic question. Honestly, I'm not entirely sure myself. Just kidding. 

## What Does This Script Do? 🤔

LoSS is a crude Python script designed to create and/or digest a wall of text, create a transcript, and send it to the OpenAI API using GPT 3.5 Turbo (by default, but feel free to change it to GPT4o if you've got deep pockets) in order to create an AI summary. 

Here's a quick rundown of how it works:

1. **Input**: You execute it in an interpreter such as VSCode, then feed it a YouTube link, a video file, an audio file, or some text.
2. **Processing**: It generates a transcript, then sends the text to the OpenAI API, which then farts out a summary.
3. **Output**: LoSS then saves this summary as a randomly named text file in the same directory as the script.

## Installation 🛠️

Install Python and requirements.txt stuff. 

1. **Step 1**: Make sure you have Python installed. If you don't, head over to [python.org](https://www.python.org/) and get that sorted. 🐍
2. **Step 2**: Open your terminal and take a deep breath.
3. **Step 3**: Navigate to the project directory. If you can't do that, I'm not sure if I can help you.
4. **Step 4**: Now, install the dependencies with this magical incantation: **pip install -r requirements.txt**

```sh
    cd path/to/your/project
```

4. **Step 4**: Now, install the dependencies with this magical incantation:

```sh
    pip install -r requirements.txt
```

If something goes wrong, don't panic! Just remember: Google is your best friend. Or your only friend when it comes to debugging. 💻

## Usage 🎬

Using LoSS is a bit like trying to herd cats. 🐱 But don't worry, I'll guide you through it step by step.

### Prerequisites
Before you start, you'll need an **OpenAI API key**. If you don't have one, head over to [OpenAI](https://beta.openai.com/signup/) and sign up. Once you have your key, keep it handy.

### Running the Script
**Step 1**: Run the script with:
    ```sh
    python LoSS.py --api-key YOUR_OPENAI_API_KEY
    ```
    Replace `YOUR_OPENAI_API_KEY` with your actual OpenAI API key and `"Your text here"` with the text you want to summarize.

**Step 2**: Put a video file, an audio file, or a transcriot (.txt) file into the **/input/** folder. If you want to transcribe and summarize a YouTube vide, you can ignore this step.

**Step 3**: Follow instructions.

**Step 4**: The summary will appear in the **/output/** folder. It will be a randomly named .txt file.

### Future Plans
This iteration barely technically works. Future plans are to iterate upon almost every aspect of it, provided I stay interested in the concept.

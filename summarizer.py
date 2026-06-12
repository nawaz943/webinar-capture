import os
import sys
import re
import requests
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import datetime

# --- CONFIGURATION ---
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"  # You can also use "mistral" or "phi3"
# ---------------------

def summarize_transcript(transcript_path):
    """Reads a transcript file, removes timestamps, and generates a summary via Ollama."""
    if not os.path.exists(transcript_path):
        print(f"[!] Error: Transcript file {transcript_path} not found.")
        return

    print(f"[*] Reading transcript for summarization: {transcript_path}")
    with open(transcript_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Remove timestamps and combine into a single block of text
    clean_text = " ".join([re.sub(r"\[.*?\]\s*", "", line).strip() for line in lines])
    
    # Basic length check for context window
    if len(clean_text.split()) > 6000:
        print("[!] Warning: Transcript is very long. The summary might be truncated by the LLM.")

    prompt = (
        "You are an expert technical writer specializing in HVAC and Building Sciences. Below is a transcript of a technical webinar. "
        "Please provide a detailed summary including the main topic, key takeaways, and any. "
        "specific action items or conclusions mentioned.\n\n"
        f"TRANSCRIPT:\n{clean_text}"
    )

    print(f"[*] Requesting summary from local LLM ({MODEL_NAME})...")
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        summary = response.json().get("response", "No summary generated.")

        # Save as text file
        summary_path = transcript_path.replace("_transcript.txt", "_summary.txt")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"[!] Summary successfully saved to: {summary_path}")

        # Save as PDF file
        summary_path_pdf = transcript_path.replace("_transcript.txt", "_summary.pdf")
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_font("Helvetica", 'B', 16)
        pdf.cell(0, 10, "Webinar Technical Summary", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", 'I', 10)
        pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(10)

        # Content
        pdf.set_font("Helvetica", size=11)
        clean_summary = summary.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 8, text=clean_summary)
        
        pdf.output(summary_path_pdf)
        print(f"[!] Summary successfully saved to: {summary_path_pdf}")
    except Exception as e:
        print(f"[!] Error connecting to Ollama: {e}. Is Ollama running?")

if __name__ == "__main__":
    # If no arguments are provided, try to use the default transcript file
    if len(sys.argv) == 1:
        default_transcript = os.path.join("./webinar_output", "webinar_audio_transcript.txt")
        print(f"[*] No arguments provided. Using default transcript: {default_transcript}")
        if not os.path.exists(default_transcript):
            print(f"[!] Error: Default transcript file '{default_transcript}' not found.")
            print("Usage: python summarizer.py <path_to_transcript_txt>")
            sys.exit(1)
        summarize_transcript(default_transcript)
    elif len(sys.argv) == 2:
        summarize_transcript(sys.argv[1])
    else:
        print("Usage: python summarizer.py <path_to_transcript_txt>")
        print("Or run without arguments to use default './webinar_output/webinar_audio_transcript.txt'.")
        sys.exit(1)
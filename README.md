# ArcVault Health Companion

> Closing the Care Loop: Full-Lifecycle Patient Agents with HAI-DEF

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)

## Overview

ArcVault Health Companion is an advanced health companion application designed to close the care loop by integrating AI-driven patient agents. It leverages Google's HAI-DEF (Healthcare AI Data Embedding Framework) models to provide intelligent support across various stages of patient care, from home triage to monitoring.

## Prerequisites

*   **Python 3.10+**
*   **HuggingFace Account & Token**: Required to download the gated medical AI models.
    *   [Sign up for HuggingFace](https://huggingface.co/join)
    *   [Generate a User Access Token](https://huggingface.co/settings/tokens) (Read access is sufficient)
    *   **Important**: You must visit the model pages (lines 63-122 in `download_models.py`) and accept the license agreements for each model (e.g., `google/medgemma-1.5-4b-it`, `google/txgemma-2b-predict`, etc.).

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd Full-Lifecycle_Health_Companion
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Model Setup

This application relies on specific pre-trained models. You need to download them before running the application.

1.  **Set your HuggingFace Token:**
    You can set it as an environment variable or pass it directly to the script.
    ```bash
    # Windows (PowerShell)
    $env:HF_TOKEN = "your_hf_token_here"
    
    # Windows (CMD)
    set HF_TOKEN=your_hf_token_here
    
    # Linux/Mac
    export HF_TOKEN=your_hf_token_here
    ```

2.  **Download Models:**
    Run the download script to fetch the smallest recommended models per modality (~17GB total).
    ```bash
    python download_models.py
    # Or pass the token directly:
    python download_models.py --token your_hf_token_here
    ```
    *   Use `--list` to see which models will be downloaded.
    *   Use `--skip-gguf` to skip downloading quantized GGUF models if you don't need them.

## Running the Application

Start the application server:
```bash
python server.py
```

Once the server is running, open your web browser and navigate to:
`http://127.0.0.1:8000`

API documentation is available at `http://127.0.0.1:8000/docs`.

## Project Structure

*   `server.py`: FastAPI backend that serves the web interface and handles API requests.
*   `static/`: Directory containing the frontend HTML, CSS, and JavaScript files.
*   `download_models.py`: Utility script to download necessary AI models from HuggingFace.
*   `strategies/`: Contains the logic for different care stages (Home Triage, Intake, Consult, Pharmacy, Monitoring).
*   `ml_models/`: Directory where downloaded models are stored (created after running the download script).
*   `data/`: Directory for storing application data, databases, and uploads.

# PhishForge with Ollama

A lightweight web application that generates Microsoft Attack Simulation templates using locally-run Ollama LLM models. PhishForge helps security teams create realistic phishing scenarios that can be manually uploaded to Microsoft's Attack Simulation Training platform.

## Features

- Simple web interface for creating simulation templates
- Local AI content generation using Ollama
- Pre-defined email templates for common phishing scenarios
- Email preview functionality
- JSON export for manual upload to Microsoft Attack Simulator
- No API keys or external services required

## Prerequisites

- Python 3.7+
- [Ollama](https://ollama.ai/) installed locally
- A compatible LLM model pulled in Ollama (e.g., llama3, mistral, etc.)

## Installation

### 1. Install Ollama

Follow the installation instructions for your platform at [ollama.ai](https://ollama.ai/download).

### 2. Pull an LLM Model

After installing Ollama, pull a model:

```
ollama pull llama3
```

Other good options include `mistral`, `gemma:2b`, or any model that works well with structured output.

### 3. Start Ollama

Make sure Ollama is running:

```
ollama serve
```

### 4. Set Up PhishForge

1. Clone the repository or download the files
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Configure the model (optional):
   ```
   export OLLAMA_MODEL=llama3
   ```
   
   On Windows:
   ```
   set OLLAMA_MODEL=llama3
   ```

4. Run the application:
   ```
   python app.py
   ```

5. Open your browser and navigate to: http://localhost:5000

## How to Use

1. **Start Ollama**:
   - Make sure Ollama is running with your preferred model

2. **Fill out the form**:
   - Enter a name for your simulation
   - Select the attack technique
   - Set the duration
   - Enter target email addresses (one per line)
   - Choose a template or generate content with Ollama

3. **Generate content with Ollama** (if selected):
   - Describe the phishing scenario you want to create
   - Click "Generate Content with Ollama"
   - Review the generated email

4. **Preview the email** (optional):
   - Click the "Preview Email" button to see how the email will appear

5. **Generate the template**:
   - Click "Generate Template" to create the JSON template

6. **Export the template**:
   - Click "Download JSON" to save the template file

7. **Upload to Microsoft**:
   - Manually upload the JSON template to the Microsoft Attack Simulator

## Customizing Templates

You can modify the pre-defined templates in the `app.py` file. Look for the `TEMPLATES` dictionary and adjust the email content as needed.

## Environment Variables

The following environment variables can be set to customize PhishForge:

- `OLLAMA_BASE_URL`: URL for your Ollama instance (default: http://localhost:11434)
- `OLLAMA_MODEL`: Default model to use (default: llama3)
- `PORT`: Port to run the Flask app on (default: 5000)

## Troubleshooting

- **Ollama Not Running**: Ensure Ollama is running by executing `ollama serve` in a terminal
- **Model Not Found**: Make sure you've pulled the model with `ollama pull modelname`
- **Poor Content Generation**: Try a different model - some models are better at structured output than others
- **Application Not Starting**: Check the console output for errors

## License

MIT

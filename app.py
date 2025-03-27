from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import json
import requests
import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='')

# Ollama configuration
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:27b")

# Pre-defined templates
TEMPLATES = {
    "password_reset": {
        "email_content": {
            "sender_name": "IT Department",
            "sender_email": "it-support@company.com",
            "subject": "Urgent: Password Reset Required",
            "body": "<p>Dear User,</p><p>Our security system has detected unusual login attempts on your account. To protect your data, we have temporarily locked your account.</p><p>Please reset your password immediately by clicking the link below:</p><p><a href='#'>[RESET PASSWORD]</a></p><p>If you do not reset your password within 24 hours, your account may be suspended.</p><p>Thank you,<br>IT Security Team</p>"
        }
    },
    "invoice": {
        "email_content": {
            "sender_name": "Accounts Department",
            "sender_email": "invoices@company.com",
            "subject": "Invoice #INV-2023-4872 Due for Payment",
            "body": "<p>Hello,</p><p>Please find attached the invoice #INV-2023-4872 for $1,249.99 due for payment by 03/30/2025.</p><p>To view and pay this invoice online, please click here: <a href='#'>[VIEW INVOICE]</a></p><p>If you have any questions regarding this invoice, please contact our accounts team.</p><p>Regards,<br>Accounts Department</p>"
        }
    },
    "shared_doc": {
        "email_content": {
            "sender_name": "OneDrive Sharing",
            "sender_email": "sharing@onedrive.com",
            "subject": "Document Shared: Q1 Financial Report",
            "body": "<p>Hi there,</p><p>John Smith (john.smith@company.com) has shared a document with you:</p><p><strong>Q1 Financial Report.xlsx</strong></p><p><a href='#'>[VIEW DOCUMENT]</a></p><p>This link will expire in 7 days.</p><p>The Microsoft OneDrive Team</p>"
        }
    }
}

@app.route('/')
def index():
    """Serve the main application HTML."""
    return send_from_directory('static', 'index.html')

@app.route('/api/generate-template', methods=['POST'])
def generate_template():
    """Generate a simulation template based on user inputs."""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        # Extract form data
        name = data.get('name', 'Untitled Simulation')
        attack_technique = data.get('attack_technique', 'credentialHarvesting')
        duration = int(data.get('duration', 7))
        targets = data.get('targets', [])
        
        # Determine email content
        if data.get('content_type') == 'template':
            template_id = data.get('template_id', 'password_reset')
            email_content = TEMPLATES.get(template_id, TEMPLATES['password_reset'])['email_content']
        else:
            # Use AI-generated content if available, or fallback to default
            email_content = data.get('generated_content', TEMPLATES['password_reset']['email_content'])
        
        # Create the Microsoft-compatible template
        template = {
            "displayName": name,
            "attackTechnique": attack_technique,
            "durationInDays": duration,
            "status": "draft",
            "includedAccountTarget": {
                "@odata.type": "#microsoft.graph.addressBookAccountTargetContent",
                "type": "addressBook",
                "accountTargetEmails": targets
            },
            "trainingSetting": {
                "settingType": "noTraining"
            },
            # Placeholders for Microsoft resources - these would be replaced during manual upload
            "payload@odata.bind": "https://graph.microsoft.com/v1.0/security/attacksimulation/payloads/placeholder",
            "loginPage@odata.bind": "https://graph.microsoft.com/v1.0/security/attacksimulation/loginPages/placeholder",
            "landingPage@odata.bind": "https://graph.microsoft.com/v1.0/security/attacksimulation/landingPages/placeholder",
            
            # Add email content for reference (not part of Microsoft schema but useful for manual creation)
            "_emailContent": email_content
        }
        
        return jsonify(template)
    
    except Exception as e:
        logger.error(f"Error generating template: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-content', methods=['POST'])
def generate_content():
    """Generate phishing email content using Ollama."""
    data = request.json
    if not data or 'scenario' not in data:
        return jsonify({"error": "No scenario provided"}), 400
    
    scenario = data.get('scenario')
    attack_technique = data.get('attack_technique', 'credentialHarvesting')
    
    try:
        # Get content from Ollama
        content = generate_with_ollama(scenario, attack_technique)
        
        # Add metadata
        content["generated_at"] = datetime.datetime.now().isoformat()
        
        return jsonify(content)
        
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}", exc_info=True)
        # Return a fallback template based on keywords
        return jsonify(get_fallback_template(scenario, attack_technique)), 200

@app.route('/api/ollama-status', methods=['GET'])
def check_ollama_status():
    """Check if Ollama is running and what models are available."""
    try:
        # Check if Ollama is running
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            return jsonify({
                "status": "running",
                "models": [model.get('name') for model in models],
                "current_model": OLLAMA_MODEL
            })
        else:
            return jsonify({"status": "error", "message": "Ollama is running but returned an error"})
    except requests.exceptions.RequestException:
        return jsonify({"status": "not_running", "message": "Ollama service not reachable"})

def generate_with_ollama(scenario, attack_technique):
    """Generate content using Ollama LLM."""
    logger.info(f"Generating phishing content with Ollama using model: {OLLAMA_MODEL}")
    
    # Build the prompt based on the attack technique
    technique_details = get_technique_details(attack_technique)
    
    prompt = f"""
    Generate a phishing email for a security awareness training simulation. 
    
    Scenario: {scenario}
    
    Attack technique: {attack_technique} - {technique_details}
    
    Return a JSON object with this exact structure:
    {{
        "sender_name": "Name of the sender",
        "sender_email": "phishing@example.com",
        "subject": "Email subject line",
        "body": "Email body with HTML formatting"
    }}
    
    The email should be convincing but include subtle signs that it's phishing.
    """
    
    try:
        # Call Ollama API
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 1024
                }
            },
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"Ollama API error: {response.status_code} - {response.text}")
            raise Exception(f"Ollama API returned status code {response.status_code}")
        
        # Extract the generated text
        generated_text = response.json().get('response', '')
        
        # Find and extract JSON from the response
        json_start = generated_text.find('{')
        json_end = generated_text.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            # If no JSON found, create a structured response from the text
            logger.warning("No valid JSON found in Ollama response, using fallback")
            return get_fallback_template(scenario, attack_technique)
        
        json_str = generated_text[json_start:json_end]
        
        try:
            content = json.loads(json_str)
            # Validate required fields
            required_fields = ["sender_name", "sender_email", "subject", "body"]
            for field in required_fields:
                if field not in content:
                    content[field] = get_fallback_template(scenario, attack_technique)[field]
            
            # Ensure HTML formatting in body
            if "<p>" not in content["body"] and "<div>" not in content["body"]:
                # Use the corrected line that avoids the f-string with backslash issue
                body_text = content['body'].replace(r'\n', '</p><p>')
                content["body"] = "<p>" + body_text + "</p>"
            
            return content
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from Ollama response: {json_str}")
            return get_fallback_template(scenario, attack_technique)
        
    except Exception as e:
        logger.error(f"Error calling Ollama: {str(e)}", exc_info=True)
        return get_fallback_template(scenario, attack_technique)

def get_technique_details(attack_technique):
    """Get details about a specific attack technique."""
    techniques = {
        "credentialHarvesting": "Tricks users into entering their username and password on a fake site",
        "malwareAttachment": "Convinces users to download and open a malicious attachment",
        "linkInAttachment": "Tricks users into opening an attachment that contains phishing links",
        "driveByUrl": "Persuades users to visit a malicious website",
        "oauth": "Tricks users into granting permissions to a malicious application"
    }
    return techniques.get(attack_technique, "Phishing attack")

def get_fallback_template(scenario, attack_technique):
    """Generate a fallback template based on scenario keywords."""
    # Simple keyword matching for fallback
    if "password" in scenario.lower() or "reset" in scenario.lower() or "account" in scenario.lower():
        return {
            "sender_name": "IT Security Team",
            "sender_email": "it-security@company.com",
            "subject": "Critical: Your Password Will Expire Today",
            "body": "<p>Dear Valued Employee,</p><p>Our security system indicates that your password will <strong>expire in the next 2 hours</strong>. To ensure uninterrupted access to company resources, you must update your password immediately.</p><p><a href='#'>Update Password Now</a></p><p>Thank you,<br>IT Security Team</p>"
        }
    elif "invoice" in scenario.lower() or "payment" in scenario.lower() or "finance" in scenario.lower():
        return {
            "sender_name": "Accounting Department",
            "sender_email": "accounting@company.com",
            "subject": "Outstanding Invoice Requires Immediate Payment",
            "body": "<p>Hello,</p><p>Our records indicate that invoice #INV-39281 for $3,742.50 is past due. Please process this payment immediately to avoid service interruption.</p><p><a href='#'>View and Pay Invoice</a></p><p>Regards,<br>Accounting Department</p>"
        }
    elif "document" in scenario.lower() or "share" in scenario.lower() or "file" in scenario.lower():
        return {
            "sender_name": "OneDrive Sharing",
            "sender_email": "onedrive@microsoft-sharing.com",
            "subject": "Important Document Shared With You",
            "body": "<p>Hello,</p><p>A document titled \"Confidential Report\" has been shared with you.</p><p>This document requires your review and signature.</p><p><a href='#'>View Document</a></p><p>The link will expire in 24 hours.</p><p>Microsoft OneDrive Team</p>"
        }
    else:
        return {
            "sender_name": "System Administrator",
            "sender_email": "admin@company.com",
            "subject": "Important: Action Required",
            "body": "<p>Dear User,</p><p>This is an important notification requiring your immediate attention. Please click the link below to address this matter.</p><p><a href='#'>Click here to respond</a></p><p>Regards,<br>System Administrator</p>"
        }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
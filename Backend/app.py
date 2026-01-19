from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize Anthropic client
client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

@app.route('/')
def home():
    return jsonify({
        "message": "Arabic Tutor API is running!",
        "status": "ok",
        "endpoints": {
            "/api/chat": "POST - Send messages to the AI tutor",
            "/api/health": "GET - Check server health"
        }
    })

@app.route('/api/health')
def health():
    return jsonify({"status": "healthy", "service": "Arabic Tutor API"})

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        # Get data from request
        data = request.json
        print(f"Received request data: {data}")  # Debug log
        
        messages = data.get('messages', [])
        system_prompt = data.get('system', '')
        max_tokens = data.get('max_tokens', 1024)
        
        if not messages:
            print("ERROR: No messages provided")
            return jsonify({"error": "No messages provided"}), 400
        
        print(f"Calling Claude API with {len(messages)} messages...")
        
        # Call Claude API
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages
        )
        
        # Extract the response text
        assistant_message = response.content[0].text
        print(f"Success! Got response: {assistant_message[:100]}...")
        
        return jsonify({
            "success": True,
            "message": assistant_message,
            "model": "claude-sonnet-4-5-20250929"
        })
        
    except anthropic.APIError as e:
        error_msg = f"Anthropic API error: {str(e)}"
        print(f"ERROR: {error_msg}")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {e.__dict__}")
        return jsonify({
            "success": False,
            "error": error_msg
        }), 500
        
    except Exception as e:
        error_msg = f"Server error: {str(e)}"
        print(f"ERROR: {error_msg}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": error_msg
        }), 500

if __name__ == '__main__':
    # Check if API key is set
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("WARNING: ANTHROPIC_API_KEY environment variable not set!")
        print("Please create a .env file with your API key")
    else:
        print("✓ API key loaded successfully")
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)

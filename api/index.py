from flask import Flask, request, jsonify, send_from_directory, make_response
import requests
import hashlib
import os
import time
from flask_cors import CORS
import traceback
# Import your story_nodes, other helpers (modified to remove pygame)
# MAKE SURE Pillow is installed for manga generation later
# from PIL import Image, ImageDraw # If doing manga server-side

app = Flask(__name__)
CORS(app, origins=["*"], methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type", "Authorization"])  # Enable CORS for all routes

# --- Constants (Remove Pygame colors/fonts) ---
POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt/"
IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 1024
IMAGE_MODEL = 'flux'
# ... other non-pygame constants ...
# ... your story_nodes dictionary ...

# --- Game Story Nodes: City of Better Choices (VeChain/VeBetter themed) ---
story_nodes = {
    "start": {
        "situation": "A new day in City of Better Choices. Your goal: lower CO2, plastic, water, and energy use. Where do you start?",
        "prompt": "Modern sustainable city morning, people choosing eco actions, reusable mugs, bikes, recycling, bright hopeful style",
        "seed": 10101,
        "choices": [
            {"text": "Grab coffee with a reusable mug (Mugshot style)", "next_node": "commute", "impact": {"co2_kg": -0.05, "plastic_g": -15, "water_l": -0.5, "energy_kwh": 0}, "tag": "reuse"},
            {"text": "Disposable cup on the go", "next_node": "commute", "impact": {"co2_kg": 0.03, "plastic_g": 15, "water_l": 0.3, "energy_kwh": 0.01}, "tag": "waste"}
        ]
    },
    "commute": {
        "situation": "Commute time. Options flood in: transit, bike, rideshare, or solo car?",
        "prompt": "City commute choices, bicycles, tram, rideshare pool, solo cars, sustainability infographic style",
        "seed": 20202,
        "choices": [
            {"text": "Bike to work", "next_node": "lunch", "impact": {"co2_kg": -2.0, "plastic_g": 0, "water_l": 0, "energy_kwh": 0.05}, "tag": "active"},
            {"text": "Take public transit", "next_node": "lunch", "impact": {"co2_kg": -1.2, "plastic_g": 0, "water_l": 0, "energy_kwh": 0.2}, "tag": "transit"},
            {"text": "Rideshare pool", "next_node": "lunch", "impact": {"co2_kg": -0.5, "plastic_g": 0, "water_l": 0, "energy_kwh": 0.3}, "tag": "shared"},
            {"text": "Drive solo", "next_node": "lunch", "impact": {"co2_kg": 2.5, "plastic_g": 0, "water_l": 0, "energy_kwh": 0.8}, "tag": "solo"}
        ]
    },
    "lunch": {
        "situation": "Lunch break. Menu choices impact your footprint.",
        "prompt": "Cafeteria with plant-forward meals, local produce, takeout plastics vs reusables, clean design",
        "seed": 30303,
        "choices": [
            {"text": "Plant-forward bowl, dine-in reusables", "next_node": "afternoon", "impact": {"co2_kg": -1.0, "plastic_g": -10, "water_l": -50, "energy_kwh": -0.1}, "tag": "plant"},
            {"text": "Local chicken wrap, no extra packaging", "next_node": "afternoon", "impact": {"co2_kg": -0.3, "plastic_g": -5, "water_l": -10, "energy_kwh": 0}, "tag": "local"},
            {"text": "Fast-food combo with plastics", "next_node": "afternoon", "impact": {"co2_kg": 0.8, "plastic_g": 25, "water_l": 30, "energy_kwh": 0.2}, "tag": "plastic"}
        ]
    },
    "afternoon": {
        "situation": "Afternoon at home. Energy decisions time.",
        "prompt": "Home energy scene with insulation, smart thermostat, solar panels, laundry choices",
        "seed": 40404,
        "choices": [
            {"text": "Run laundry cold + line-dry", "next_node": "evening", "impact": {"co2_kg": -0.4, "plastic_g": 0, "water_l": -5, "energy_kwh": -0.6}, "tag": "efficient"},
            {"text": "Adjust thermostat +1°C/+2°F", "next_node": "evening", "impact": {"co2_kg": -0.3, "plastic_g": 0, "water_l": 0, "energy_kwh": -0.8}, "tag": "thermostat"},
            {"text": "Ignore and blast AC", "next_node": "evening", "impact": {"co2_kg": 0.6, "plastic_g": 0, "water_l": 0, "energy_kwh": 1.2}, "tag": "waste_energy"}
        ]
    },
    "evening": {
        "situation": "Community time. Will you give back?",
        "prompt": "Neighborhood cleanup, recycling center, repair café, lively community vibe",
        "seed": 50505,
        "choices": [
            {"text": "Join a river cleanup (Cleanify style)", "next_node": "_calculate_end", "impact": {"co2_kg": 0, "plastic_g": -500, "water_l": 0, "energy_kwh": 0}, "tag": "cleanup"},
            {"text": "Host repair café: fix 2 gadgets", "next_node": "_calculate_end", "impact": {"co2_kg": -1.5, "plastic_g": -100, "water_l": 0, "energy_kwh": -0.2}, "tag": "repair"},
            {"text": "Skip community plans", "next_node": "_calculate_end", "impact": {"co2_kg": 0.2, "plastic_g": 0, "water_l": 0, "energy_kwh": 0.1}, "tag": "skip"}
        ]
    },
    "good_end": {"is_end": True, "ending_category": "Eco Champion", "situation": "Your day reshaped the city’s footprint. The DAO praises your impact.", "prompt": "City celebration of eco champion, dashboards showing falling CO2 and plastic"},
    "neutral_end": {"is_end": True, "ending_category": "Balanced Citizen", "situation": "Some wins, some losses. You nudged the city greener.", "prompt": "City dashboard with mixed metrics, hopeful tone"},
    "bad_end": {"is_end": True, "ending_category": "Needs Improvement", "situation": "The city trends worse today—tomorrow offers another chance.", "prompt": "City metrics rising, smoggy dusk, call to action"}
}

# --- Game State (In-memory - BAD for multiple users/production) ---
game_state = {
    "current_node_id": "start",
    "story_path": [], # Store tuples: (node_id, choice_text, score_mod)
    "current_score": 0,
    "sentiment_tally": {},
    "impacts": {"co2_kg": 0.0, "plastic_g": 0.0, "water_l": 0.0, "energy_kwh": 0.0},
    "last_error": None,
    "last_reset": time.time()  # Track when the game was last reset
}

# Add a user_sessions dictionary to track individual user sessions
user_sessions = {}

# --- Helper Functions (Refactored - NO PYGAME) ---
def get_dynamic_seed(base_seed, path_node_ids, session_id=None):
    """Generate a unique seed based on the path taken and session ID"""
    if not session_id:
        # Use existing path-based seed if no session ID
        path_hash = hashlib.md5(''.join(path_node_ids).encode()).hexdigest()
        seed = (base_seed + int(path_hash, 16)) % 999999
    else:
        # Create a unique seed combining base seed, path, and session ID
        combined = f"{base_seed}-{''.join(path_node_ids)}-{session_id}"
        seed_hash = hashlib.md5(combined.encode()).hexdigest()
        seed = int(seed_hash, 16) % 999999
    
    return seed

def enhance_prompt(base_prompt, path_tuples, sentiment_tally, last_choice, session_id=None):
    """Enhance the base prompt with unique elements based on the user's journey"""
    # Get the user's style preferences (if stored in their session)
    style_elements = []
    if session_id and session_id in user_sessions and 'style_preferences' in user_sessions[session_id]:
        style_elements = user_sessions[session_id]['style_preferences']
    
    # Default style elements if none are set
    if not style_elements:
        style_elements = ["detailed", "fantasy", "ethereal"]
    
    # Add sentiment-based modifiers
    if sentiment_tally.get('kind', 0) > sentiment_tally.get('selfish', 0):
        style_elements.append("warm light")
    else:
        style_elements.append("cool tones")
        
    if sentiment_tally.get('adventurous', 0) > 1:
        style_elements.append("vibrant")
    
    if sentiment_tally.get('cautious', 0) > 1:
        style_elements.append("muted colors")
    
    # Add a unique element based on session ID if available
    if session_id:
        # Use the session ID to deterministically select unique style elements
        session_hash = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
        
        # List of potential style modifiers to make images unique
        unique_styles = [
            "cinematic lighting", "golden hour", "blue hour", "mist", 
            "ray tracing", "dramatic shadows", "soft focus", "high contrast",
            "low saturation", "high saturation", "dreamlike", "surreal",
            "watercolor style", "oil painting style", "concept art", "digital art"
        ]
        
        # Select 1-3 unique styles based on session ID
        num_styles = 1 + (session_hash % 3)  # 1 to 3 styles
        for i in range(num_styles):
            style_index = (session_hash + i) % len(unique_styles)
            style_elements.append(unique_styles[style_index])
    
    # Combine everything into an enhanced prompt
    enhanced = f"{base_prompt}, {', '.join(style_elements)}"
    
    # Make each image different even for the same node by adding timestamp
    timestamp = int(time.time())
    enhanced += f", seed:{timestamp}"
    
    return enhanced

def score_from_impact(impact_delta):
    """Compute a score delta from an impact change using simple weights.
    Negative values (reductions) increase score; positive values decrease it.
    """
    co2 = impact_delta.get("co2_kg", 0) or 0
    plastic = impact_delta.get("plastic_g", 0) or 0
    water = impact_delta.get("water_l", 0) or 0
    energy = impact_delta.get("energy_kwh", 0) or 0
    # Benefits (negative deltas)
    benefit = max(0, -co2) * 1.0 + max(0, -plastic) / 50.0 + max(0, -water) / 10.0 + max(0, -energy) * 0.5
    # Harms (positive deltas)
    harm = max(0, co2) * 1.0 + max(0, plastic) / 50.0 + max(0, water) / 10.0 + max(0, energy) * 0.5
    return round(benefit - harm, 2)

def reset_game_state(session_id=None):
    """Reset the game state"""
    initial_state = {
        "current_node_id": "start",
        "path_history": ["start"],
        "score": 0,
        "sentiment_tally": {},
        "choice_history": [],
        "impacts": {"co2_kg": 0.0, "plastic_g": 0.0, "water_l": 0.0, "energy_kwh": 0.0},
        "created_at": time.time()
    }
    
    # If we have a session ID, store the state in the user_sessions dictionary
    if session_id:
        if session_id not in user_sessions:
            user_sessions[session_id] = {}
        
        # Generate some random style preferences for this session
        import random
        all_style_options = [
            "fantasy", "medieval", "ethereal", "mystical", "dramatic", 
            "whimsical", "dark", "bright", "colorful", "muted"
        ]
        user_sessions[session_id]['style_preferences'] = random.sample(all_style_options, 3)
        user_sessions[session_id]['state'] = initial_state
        return user_sessions[session_id]['state']
    
    return initial_state

def get_node_details(node_id):
    """Get details for a story node with personalized content"""
    try:
        # Get base node
        node = story_nodes.get(node_id)
        if not node:
            return None
            
        # Make a copy so we don't modify the original
        node_copy = node.copy()
        
        # Personalize choices if we're not at an end node
        if not node_copy.get("is_end", False) and "choices" in node_copy:
            # Deep copy choices to avoid modifying original
            node_copy["choices"] = [choice.copy() for choice in node_copy["choices"]]
            
            # Personalize choice texts with small variations
            for choice in node_copy["choices"]:
                if "text" in choice:
                    # We could add small variations to choice text here
                    # But we'll keep the first choice consistent as required
                    pass  # Implemented in the next update
        
        return node_copy
        
    except Exception as e:
        traceback.print_exc()
        return None

# --- API Endpoints ---
@app.route('/')
def serve_index():
    try:
        return send_from_directory('../public', 'index.html')
    except Exception as e:
        print(f"Error serving index: {str(e)}")
        # Fallback response
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>City of Better Choices</title>
        </head>
        <body>
            <h1>City of Better Choices</h1>
            <p>Loading game...</p>
            <script>
                // Redirect to API test
                fetch('/api/test')
                    .then(response => response.json())
                    .then(data => console.log('API Status:', data))
                    .catch(error => console.error('API Error:', error));
            </script>
        </body>
        </html>
        """, 200

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "message": "City of Better Choices API is running"})

@app.route('/api/test')
def test_endpoint():
    return jsonify({"message": "API is working", "timestamp": time.time()})

@app.route('/<path:path>')
def serve_static(path):
    try:
        return send_from_directory('../public', path)
    except Exception as e:
        print(f"Error serving static file {path}: {str(e)}")
        return f"Error serving file: {str(e)}", 404

@app.route('/api/state', methods=['GET'])
def get_current_state():
    try:
        # Get user's session ID from cookies or create a new one
        session_id = request.cookies.get('session_id')
        if not session_id:
            # Generate a new session ID
            import secrets
            session_id = hashlib.md5(f"{time.time()}-{secrets.token_hex(8)}".encode()).hexdigest()
        
        # Get or create the user's game state
        if session_id in user_sessions and 'state' in user_sessions[session_id]:
            game_state = user_sessions[session_id]['state']
        else:
            game_state = reset_game_state(session_id)
        
        current_node_id = game_state["current_node_id"]
        node_details = get_node_details(current_node_id)
        
        if not node_details:
            # Migrate legacy nodes from older theme by resetting to start
            legacy_nodes = {
                "generic_good_ending", "generic_neutral_ending", "generic_bad_ending",
                "heroic_savior_ending", "wise_mage_ending", "forest_guardian_ending",
                "peaceful_traveler_ending", "forest_explorer_ending", "merchant_ending",
                "lost_soul_ending", "cursed_wanderer_ending", "forest_prisoner_ending",
                "deep_forest", "grateful_creature", "hidden_treasure", "amulet_power",
                "forest_edge", "lost_forest", "lost_deeper", "tree_climb", "creature_guidance",
                "stone_circle", "wise_decision", "village_arrival", "cave_entrance"
            }
            if current_node_id in legacy_nodes:
                # reset to new start
                game_state = reset_game_state(session_id)
                current_node_id = game_state["current_node_id"]
                node_details = get_node_details(current_node_id)
            else:
                return jsonify({"error": "Invalid node"}), 400
        
        # Generate image URL with dynamic seed and enhanced prompt
        path_node_ids = game_state.get("path_history", [])
        sentiment_tally = game_state.get("sentiment_tally", {})
        choice_history = game_state.get("choice_history", [])
        last_choice = choice_history[-1] if choice_history else None
        
        base_seed = node_details.get("seed", 12345)
        dynamic_seed = get_dynamic_seed(base_seed, path_node_ids, session_id)
        
        path_tuples = [(node, game_state.get("sentiment_tally", {}).get(node, 0)) 
                       for node in path_node_ids]
        
        base_prompt = node_details.get("prompt", "")
        enhanced_prompt = enhance_prompt(base_prompt, path_tuples, sentiment_tally, last_choice, session_id)
        
        # Create the image URL
        encoded_prompt = requests.utils.quote(enhanced_prompt)
        image_url = f"{POLLINATIONS_BASE_URL}{encoded_prompt}?model={IMAGE_MODEL}&width={IMAGE_WIDTH}&height={IMAGE_HEIGHT}"
        
        # Personalize choices with variations except the first choice
        choices = node_details.get("choices", [])
        if choices and len(choices) > 0:
            # Keep a deep copy to avoid modifying the original
            choices = [choice.copy() for choice in choices]
            
            # Get user's personality traits from sessions or generate new ones
            if session_id not in user_sessions:
                user_sessions[session_id] = {}
            
            if 'personality_traits' not in user_sessions[session_id]:
                # Generate random personality traits for this user
                import random
                traits = ["cautious", "bold", "diplomatic", "direct", "curious", "practical", 
                          "optimistic", "pessimistic", "detailed", "concise"]
                user_sessions[session_id]['personality_traits'] = random.sample(traits, 3)
            
            user_traits = user_sessions[session_id]['personality_traits']
            
            # Get a hash from the session ID to make choices consistently unique per user
            session_hash = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
            
            # Personalize choices (except first one at the start node) with small variations
            for i, choice in enumerate(choices):
                # Skip first choice at start node to keep it consistent
                if current_node_id == "start" and i == 0:
                    continue
                    
                original_text = choice.get("text", "")
                
                # Adjective modifiers based on personality
                adjectives = {
                    "cautious": ["carefully", "cautiously", "deliberately"],
                    "bold": ["boldly", "bravely", "confidently"],
                    "diplomatic": ["politely", "respectfully", "graciously"],
                    "direct": ["directly", "straightforwardly", "bluntly"],
                    "curious": ["curiously", "inquisitively", "wonderingly"],
                    "practical": ["practically", "sensibly", "reasonably"],
                    "optimistic": ["hopefully", "optimistically", "eagerly"],
                    "pessimistic": ["warily", "skeptically", "doubtfully"],
                    "detailed": ["meticulously", "thoroughly", "carefully"],
                    "concise": ["simply", "briefly", "efficiently"]
                }
                
                # Get suitable adjectives for this user's personality
                suitable_adjectives = []
                for trait in user_traits:
                    if trait in adjectives:
                        suitable_adjectives.extend(adjectives[trait])
                
                if suitable_adjectives:
                    # Select a consistent adjective based on session and choice
                    adj_index = (session_hash + i) % len(suitable_adjectives)
                    selected_adj = suitable_adjectives[adj_index]
                    
                    # Insert the adjective into the choice text if it makes sense
                    # Identify the verb in the choice text
                    words = original_text.split()
                    # Simple heuristic: Look for verbs typical in choices
                    common_verbs = ["Take", "Go", "Explore", "Talk", "Help", "Ignore", "Follow", "Leave", 
                                   "Examine", "Search", "Ask", "Fight", "Run", "Hide", "Climb", "Jump"]
                    
                    for j, word in enumerate(words):
                        if word in common_verbs and j < len(words) - 1:
                            # Insert adjective after the verb
                            modified_text = " ".join(words[:j+1]) + " " + selected_adj + " " + " ".join(words[j+1:])
                            choice["text"] = modified_text
                            break
        
        # Get the score from the game state, ensuring consistency in property names
        score = game_state.get("score", 0)
        
        # Prepare the response
        response_data = {
            "situation": node_details.get("situation", ""),
            "is_end": node_details.get("is_end", False),
            "ending_category": node_details.get("ending_category", ""),
            "choices": choices,  # Use personalized choices
            "image_url": image_url,
            "image_prompt": enhanced_prompt,
            "current_score": score,  # Use consistent name for frontend
            "score": score,  # Include both for backward compatibility
            "impacts": game_state.get("impacts", {"co2_kg":0,"plastic_g":0,"water_l":0,"energy_kwh":0})
        }
        
        # Generate special end-game content if this is an end node
        if node_details.get("is_end", False):
            # Compute governance weight from impacts (simple normalized formula)
            imp = game_state.get("impacts", {})
            # Positive impact is negative numbers for co2/plastic/water/energy
            benefit = max(0, -imp.get("co2_kg", 0)) * 1.0 \
                      + max(0, -imp.get("plastic_g", 0)) / 500.0 \
                      + max(0, -imp.get("water_l", 0)) / 50.0 \
                      + max(0, -imp.get("energy_kwh", 0)) * 0.8
            governance_weight = round(min(10.0, 2.0 + benefit), 2)
            response_data["governance_weight"] = governance_weight
            response_data["impact_summary"] = {
                "co2_kg": round(imp.get("co2_kg", 0), 3),
                "plastic_g": round(imp.get("plastic_g", 0), 1),
                "water_l": round(imp.get("water_l", 0), 1),
                "energy_kwh": round(imp.get("energy_kwh", 0), 3)
            }
            manga_prompt = f"Manga style, story summary of {enhanced_prompt}"
            encoded_manga_prompt = requests.utils.quote(manga_prompt)
            response_data["manga_image_url"] = f"{POLLINATIONS_BASE_URL}{encoded_manga_prompt}?model={IMAGE_MODEL}&width={IMAGE_WIDTH}&height={IMAGE_HEIGHT}"
            
            summary_prompt = f"Fantasy book cover, hero's journey, {enhanced_prompt}"
            encoded_summary_prompt = requests.utils.quote(summary_prompt)
            response_data["summary_image_url"] = f"{POLLINATIONS_BASE_URL}{encoded_summary_prompt}?model={IMAGE_MODEL}&width={IMAGE_WIDTH}&height={IMAGE_HEIGHT}"
        
        # Create response with cookie
        response = make_response(jsonify(response_data))
        response.set_cookie('session_id', session_id, max_age=86400*30)  # 30 days
        return response
        
    except Exception as e:
        print(f"Error in get_current_state: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/choice', methods=['POST'])
def make_choice():
    try:
        data = request.json
        choice_index = data.get('choice_index')
        
        if choice_index is None:
            return jsonify({"error": "Missing choice_index"}), 400
        
        # Get user's session ID from cookies
        session_id = request.cookies.get('session_id')
        if not session_id:
            return jsonify({"error": "No session found"}), 400
        
        # Get the user's game state
        if session_id not in user_sessions or 'state' not in user_sessions[session_id]:
            return jsonify({"error": "No game in progress"}), 400
            
        game_state = user_sessions[session_id]['state']
        current_node_id = game_state["current_node_id"]
        
        # Get current node details
        node_details = get_node_details(current_node_id)
        if not node_details:
            # If the node was from the legacy theme, reset and continue
            game_state = reset_game_state(session_id)
            current_node_id = game_state["current_node_id"]
            node_details = get_node_details(current_node_id)
            if not node_details:
                return jsonify({"error": "Invalid current node"}), 400
            
        # Validate choice index
        if not node_details.get("choices") or choice_index >= len(node_details["choices"]):
            return jsonify({"error": "Invalid choice index"}), 400
            
        # Get the chosen choice
        choice = node_details["choices"][choice_index]
        
        # Special processing for dynamic ending calculation
        next_node_id = choice.get("next_node")
        if next_node_id == "_calculate_end":
            # Determine ending based on eco impacts (City of Better Choices)
            impacts = game_state.get("impacts", {"co2_kg":0,"plastic_g":0,"water_l":0,"energy_kwh":0})
            benefit = max(0, -impacts.get("co2_kg", 0)) * 1.0 \
                      + max(0, -impacts.get("plastic_g", 0)) / 500.0 \
                      + max(0, -impacts.get("water_l", 0)) / 50.0 \
                      + max(0, -impacts.get("energy_kwh", 0)) * 0.8
            harm = max(0, impacts.get("co2_kg", 0)) * 1.0 \
                   + max(0, impacts.get("plastic_g", 0)) / 500.0 \
                   + max(0, impacts.get("water_l", 0)) / 50.0 \
                   + max(0, impacts.get("energy_kwh", 0)) * 0.8
            if benefit - harm >= 2.0:
                next_node_id = "good_end"
            elif harm - benefit >= 1.0:
                next_node_id = "bad_end"
            else:
                next_node_id = "neutral_end"

        # Fallback if next node is missing
        if next_node_id not in story_nodes:
            next_node_id = "neutral_end"
        
        # Update game state
        game_state["current_node_id"] = next_node_id
        game_state["path_history"].append(next_node_id)
        
        # Update impacts and derive score from eco changes
        if "impacts" not in game_state or not isinstance(game_state["impacts"], dict):
            game_state["impacts"] = {"co2_kg": 0.0, "plastic_g": 0.0, "water_l": 0.0, "energy_kwh": 0.0}
        impacts_delta = choice.get("impact") or {"co2_kg":0,"plastic_g":0,"water_l":0,"energy_kwh":0}
        for k, v in impacts_delta.items():
            if k not in game_state["impacts"]:
                game_state["impacts"][k] = 0
            game_state["impacts"][k] += v
        # Score is based on impact delta (benefit minus harm)
        game_state["score"] += score_from_impact(impacts_delta)
        
        # Update sentiment tally
        tag = choice.get("tag")
        if tag:
            if tag not in game_state["sentiment_tally"]:
                game_state["sentiment_tally"][tag] = 0
            game_state["sentiment_tally"][tag] += 1
        
        # Record this choice
        game_state["choice_history"].append({
            "from_node": current_node_id,
            "choice_index": choice_index,
            "choice_text": choice.get("text", ""),
            "tag": tag
        })
        
        # Save the updated state
        user_sessions[session_id]['state'] = game_state
        
        # Return the new state
        return get_current_state()
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/reset', methods=['POST'])
def reset_game():
    try:
        # Get user's session ID from cookies
        session_id = request.cookies.get('session_id')
        if not session_id:
            # Generate a new session ID
            import secrets
            session_id = hashlib.md5(f"{time.time()}-{secrets.token_hex(8)}".encode()).hexdigest()
        
        # Reset the game state for this session
        reset_game_state(session_id)
        
        # Instead of just returning success message, return the actual game state
        # by calling the get_current_state function
        return get_current_state()
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/share-image', methods=['GET'])
def generate_share_image():
    try:
        # Get user's session ID from cookies
        session_id = request.cookies.get('session_id')
        if not session_id:
            return jsonify({"error": "No session found"}), 400
        
        # Get the user's game state
        if session_id not in user_sessions or 'state' not in user_sessions[session_id]:
            return jsonify({"error": "No game in progress"}), 400
            
        game_state = user_sessions[session_id]['state']
        
        # Get score and ending information
        score = game_state.get("score", 0)
        current_node_id = game_state.get("current_node_id", "")
        node_details = get_node_details(current_node_id)
        
        if not node_details:
            return jsonify({"error": "Invalid node"}), 400
            
        # Check if the game has ended
        if not node_details.get("is_end", False):
            return jsonify({"error": "Game has not ended yet"}), 400
            
        # Get the ending category
        ending_category = node_details.get("ending_category", "Adventure Complete")
        
        # Generate the specific manga image prompt with user's journey details
        path_node_ids = game_state.get("path_history", [])
        sentiment_tally = game_state.get("sentiment_tally", {})
        
        # Generate main traits from sentiment tally
        main_traits = []
        for tag, count in sentiment_tally.items():
            if count > 0:
                main_traits.append(tag)
        
        # Select top 3 traits if we have that many
        top_traits = main_traits[:3] if len(main_traits) >= 3 else main_traits
        traits_text = ", ".join(top_traits)
        
        # Create a personalized story description
        personality = f"a {traits_text} adventurer" if traits_text else "an adventurer"
        
        # Generate image URL with enhanced prompt
        base_prompt = node_details.get("prompt", "")
        path_tuples = [(node, sentiment_tally.get(node, 0)) for node in path_node_ids]
        choice_history = game_state.get("choice_history", [])
        last_choice = choice_history[-1] if choice_history else None
        
        # Get dynamic seed
        base_seed = node_details.get("seed", 12345)
        dynamic_seed = get_dynamic_seed(base_seed, path_node_ids, session_id)
        
        # Generate enhanced prompt for manga-style image
        enhanced_prompt = enhance_prompt(base_prompt, path_tuples, sentiment_tally, last_choice, session_id)
        
        # Create manga-style panel layout prompt
        share_manga_prompt = f"Manga style, 4-panel comic strip telling the story of {personality} who achieved the '{ending_category}' ending with a score of {score}, {enhanced_prompt}, clean white background with title 'City of Better Choices' and score displayed"
        
        # URL encode the prompt
        encoded_manga_prompt = requests.utils.quote(share_manga_prompt)
        share_image_url = f"{POLLINATIONS_BASE_URL}{encoded_manga_prompt}"
        
        # Return the share image URL
        return jsonify({
            "share_image_url": share_image_url,
            "score": score,
            "ending_category": ending_category
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Vercel expects the app object for Python runtimes
# The file is usually named index.py inside an 'api' folder
# If running locally:
if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
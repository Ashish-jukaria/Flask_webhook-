from flask import Blueprint, request, jsonify
from app.extensions import mongo
from datetime import datetime


webhook = Blueprint('Webhook', __name__, url_prefix='/webhook')

@webhook.route('/push', methods=["POST"])
def handle_push():
    if request.is_json:
        data = request.get_json()
        author = data.get('pusher', {}).get('name')
        branch = data.get('ref', '').split('/')[-1]
        commits = data.get('commits', [])

        # Process commits here
        commit_messages = [commit.get('message') for commit in commits]

        mongo.db.events.insert_one({
            "event_type": "push",
            "author": author,
            "to_branch": branch,
            "commit_messages": commit_messages,
            "timestamp": datetime.utcnow()
        })

        return jsonify({"message": "Push event stored!"}), 201
    return jsonify({"error": "Invalid JSON"}), 400

@webhook.route('/pull', methods=["POST"])
def handle_pull():
    if request.is_json:
        data = request.get_json()

        # Extract relevant information
        action = data.get('action')
        pull_request = data.get('pull_request', {})
        user_name = pull_request.get('user', {}).get('login')
        from_branch = pull_request.get('head', {}).get('ref')
        to_branch = pull_request.get('base', {}).get('ref')
        timestamp = pull_request.get('created_at')
        
        print("Action:", action)
        print("User Name:", user_name)
        print("From Branch:", from_branch)
        print("To Branch:", to_branch)
        print("Timestamp:", timestamp)
        
        if action in ['opened', 'synchronized']:  # Example actions to handle
        # Insert into MongoDB
            try:
                mongo.db.events.insert_one({
                    "event_type": "pull",
                    "action": action,
                    "user_name": user_name,
                    "from_branch": from_branch,
                    "to_branch": to_branch,
                    "timestamp": datetime.utcnow(),
                })
                return jsonify({"message": "Pull request event stored!"}), 201
            except Exception as e:
                print(f"Error inserting data: {e}")
                return jsonify({"error": "Internal Server Error"}), 500
        return jsonify({"error": "Invalid JSON"}), 400


@webhook.route('/merge', methods=["POST"])
def handle_merge():
    if request.is_json:
        data = request.get_json()

        # Extract relevant information from the pull request merge event
        action = data.get('action')  # e.g., 'closed', 'synchronize', etc.
        pull_request = data.get('pull_request', {})
        user_name = pull_request.get('user', {}).get('login')  # PR author's username
        from_branch = pull_request.get('head', {}).get('ref')  # Source branch
        to_branch = pull_request.get('base', {}).get('ref')    # Target branch
        timestamp = pull_request.get('merged_at')  # Merged time
        merged = pull_request.get('merged', False)  # Check if it is a merged event

        # Only process merge events when action is 'closed' and 'merged' is True
        if action == 'closed' and merged:
            # Print to debug (optional)
            print("Action:", action)
            print("User Name:", user_name)
            print("From Branch:", from_branch)
            print("To Branch:", to_branch)
            print("Timestamp:", timestamp)

            # Insert the merge event data into MongoDB
            try:
                mongo.db.events.insert_one({
                    "event_type": "merge",
                    "action": action,
                    "user_name": user_name,
                    "from_branch": from_branch,
                    "to_branch": to_branch,
                    "timestamp": datetime.utcnow(),
                })
                return jsonify({"message": "Merge event stored!"}), 201
            except Exception as e:
                print(f"Error inserting data: {e}")
                return jsonify({"error": "Internal Server Error"}), 500
        else:
            return jsonify({"message": "Not a merge event or already closed"}), 400
    return jsonify({"error": "Invalid JSON"}), 400



@webhook.route('/latest', methods=["GET"])
def get_latest_events():
    try:
        events = list(mongo.db.events.find().sort('timestamp', -1).limit(10))
        for event in events:
            event['_id'] = str(event['_id'])  # Convert ObjectId to string
        return jsonify(events)
    except Exception as e:
        # Log the error and return a generic error message
        print(f"Error fetching events: {e}")
        return jsonify({"error": "An error occurred while fetching events."}), 500


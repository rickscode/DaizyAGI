import os
import openai
import json
from googleapiclient.discovery import build
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
# openai.Model.list()



load_dotenv()

# Set up OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set up Google API
google_api_key = os.getenv("GOOGLE_API_KEY")
custom_search_engine_id = os.getenv("CUSTOM_SEARCH_ENGINE_ID")

# Set up MongoDB

uri = os.getenv("MONGODB_URI")

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

def create_database():
    client = MongoClient(uri)
    db = client["ai_data"]
    db["interactions"].create_index("id", unique=True)

def insert_interaction(input_text, action):
    client = MongoClient(uri)
    db = client["ai_data"]
    interactions = db["interactions"]

    interaction_data = {
        "input_text": input_text,
        "action": action
    }

    result = interactions.insert_one(interaction_data)
    return result.inserted_id

def generate_response(messages):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": messages}],
            max_tokens=100,
            n=1,
            stop=None,
            temperature=0.5,
        )
    except openai.error.RateLimitError:
        print("Model is currently overloaded. Please try again later.")
        return {"type": "text", "content": "Model is currently overloaded. Please try again later."}

    response_text = response.choices[0].message['content'].strip()

    action = {"type": "text", "content": response_text}  # Assign a default value to action

    try:
        action = json.loads(response_text)  # Update the value of action if response_text is a valid JSON
    except json.JSONDecodeError:
        print("")

    return action

def google_search(query, num_results=8):
    service = build("customsearch", "v1", developerKey=google_api_key)
    result = (
        service.cse()
        .list(q=query, cx=custom_search_engine_id, num=num_results)
        .execute()
    )

    search_results = result.get("items", [])
    search_results_links = [item["link"] for item in search_results]
    return search_results_links

def get_approvals(prompt):
    response = openai.Completion.create(
        model="davinci-codex",
        prompt=prompt,
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.5,
    )

    response_text = response.choices[0].text.strip()
    response_dict = json.loads(response_text)
    approval_prompt = response_dict.get("approval_prompt")

    user_approves = None
    if approval_prompt:
        print(approval_prompt)
        user_approves = input("Approve? (y/n): ")
        while user_approves.lower() not in ["y", "n"]:
            user_approves = input("Please enter 'y' or 'n': ")
    
    return user_approves

def main():
    create_database()

    input_text = input("What is my objective?: ")
    action = generate_response(input_text)  # Get the action directly from generate_response function

    if action["type"] == "text":
        print(action["content"])

    elif action["type"] == "search":
        search_results = google_search(action["query"])
        print(f"Search results:\n{search_results}")

        # Save interaction to the database
        insert_interaction(input_text, action)

    elif action["type"] == "write_file":
        # Write content to the specified file
        with open(action["file_name"], "w") as file:
            file.write(action["content"])

        print(f"Content has been written to {action['file_name']}")

        # Save interaction to the database
        insert_interaction(input_text, action)

    else:
        print("Unknown action")

if __name__ == "__main__":
    main()

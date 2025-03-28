from flask import Flask, jsonify, request
import requests
from concurrent.futures import ThreadPoolExecutor
import functools

app = Flask(__name__)

BASE_URL = "http://20.244.56.144/test"
HEADERS = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJNYXBDbGFpbXMiOnsiZXhwIjoxNzQzMTU2MjM2LCJpYXQiOjE3NDMxNTU5MzYsImlzcyI6IkFmZm9yZG1lZCIsImp0aSI6ImMyMDhjNTgxLTNmMzAtNDdhOS05MWM4LWVhNmUwZmZkYmFhYiIsInN1YiI6InBoYW5pbmRyYXJlZGR5MzEwMjMxQGdtYWlsLmNvbSJ9LCJjb21wYW55TmFtZSI6Ikxha2lSZWRkeSBCYWxpIFJlZGR5IENvbGxlZ2Ugb2YgRW5naW5lZXJpbmciLCJjbGllbnRJRCI6ImMyMDhjNTgxLTNmMzAtNDdhOS05MWM4LWVhNmUwZmZkYmFhYiIsImNsaWVudFNlY3JldCI6IkFqY3laTXR5Zm5wenlXbHAiLCJvd25lck5hbWUiOiJLYXJyaSBQaGFuaW5kcmEgUmVkZHkiLCJvd25lckVtYWlsIjoicGhhbmluZHJhcmVkZHkzMTAyMzFAZ21haWwuY29tIiwicm9sbE5vIjoiMjI3NjFBNTQyMSJ9.zDVg48uXzRzvrVJ6e7vrBD76p797O5D5FPlKZaID8UI",
}

@functools.lru_cache(maxsize=10)
def fetch_users():
    try:
        response = requests.get(f"{BASE_URL}/users", headers=HEADERS, timeout=5)
        response.raise_for_status()
        return response.json().get("users", {})
    except requests.RequestException as e:
        print(f"Error fetching users: {e}")
        return {}

def fetch_user_posts(user_id):
    try:
        response = requests.get(f"{BASE_URL}/users/{user_id}/posts", headers=HEADERS, timeout=5)
        response.raise_for_status()
        return response.json().get("posts", [])
    except requests.RequestException as e:
        print(f"Error fetching posts for user {user_id}: {e}")
        return []

def fetch_comments_count(post_id):
    try:
        response = requests.get(f"{BASE_URL}/posts/{post_id}/comments", headers=HEADERS, timeout=5)
        response.raise_for_status()
        return len(response.json().get("comments", []))
    except requests.RequestException as e:
        print(f"Error fetching comments for post {post_id}: {e}")
        return 0

@app.route('/users', methods=['GET'])
def get_top_users():
    users = fetch_users()
    if not users:
        return jsonify({"error": "Failed to fetch users"}), 500

    user_post_counts = []
    with ThreadPoolExecutor() as executor:
        results = {uid: executor.submit(fetch_user_posts, uid) for uid in users.keys()}
        for uid, future in results.items():
            user_post_counts.append((uid, users[uid], len(future.result())))

    top_users = sorted(user_post_counts, key=lambda x: x[2], reverse=True)[:5]
    return jsonify({"top_users": [{"user_id": u[0], "name": u[1], "post_count": u[2]} for u in top_users]})

@app.route('/posts', methods=['GET'])
def get_posts():
    post_type = request.args.get("type", "latest")

    users = fetch_users()
    if not users:
        return jsonify({"error": "Failed to fetch users"}), 500

    all_posts = []
    with ThreadPoolExecutor() as executor:
        user_post_futures = {uid: executor.submit(fetch_user_posts, uid) for uid in users.keys()}

        for user_id, future in user_post_futures.items():
            user_posts = future.result()
            post_futures = {p["id"]: executor.submit(fetch_comments_count, p["id"]) for p in user_posts}

            for post in user_posts:
                post["comment_count"] = post_futures[post["id"]].result()
                all_posts.append(post)

    if not all_posts:
        return jsonify({"error": "No posts available"}), 404

    if post_type == "latest":
        return jsonify({"latest_posts": sorted(all_posts, key=lambda x: x["id"], reverse=True)[:5]})
    elif post_type == "popular":
        return jsonify({"popular_posts": sorted(all_posts, key=lambda x: x["comment_count"], reverse=True)[:5]})
    else:
        return jsonify({"error": "Invalid type parameter"}), 400

if __name__ == '__main__':
    app.run(debug=True)

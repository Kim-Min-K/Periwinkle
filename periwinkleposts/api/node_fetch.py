import requests
import uuid
from urllib.parse import urlparse
from accounts.models import Authors, Post, Comment, Like
from .models import ExternalNode

def extract_uuid_from_url(url):
    """
    Extract UUID v4 from URL path
    Example: http://example.com/api/authors/67b7b9bf-d2e4-4a22-8a57-4a087a8a9b1f/ → 
    returns '67b7b9bf-d2e4-4a22-8a57-4a087a8a9b1f'
    """
    path_segments = urlparse(url).path.split('/')
    for segment in path_segments:
        try:
            uuid.UUID(segment)
            return segment
        except ValueError:
            continue
    return None  

def fetch_all_users(node):
    users = []
    page = 1
    while True:
        url = "http://[2605:fd00:4:1001:f816:3eff:fe31:2dc6]:8000/api/authors"
        response = requests.get(url, auth=(node.username, node.password))
        if response.status_code != 200:
            break
            
        data = response.json()
        users.extend(data.get('authors', []))
        
        if len(data.get('authors', [])) < 20:
            break
        page += 1
    return users

def process_users(users_data, node):
    for user in users_data:
        user_uuid = extract_uuid_from_url(user['id'])
        if not user_uuid:
            continue
            
        Authors.objects.update_or_create(
            row_id=user_uuid,
            defaults={
                'host': user.get('host'),
                'username': user.get('displayName'),
                'github_username': user.get('github', '').split('/')[-1],
                'avatar_url': user.get('profileImage'),
                'page_url': user.get('page'),
                'is_local': False
            }
        )

# Post synchronization
def fetch_all_posts(node):
    posts = []
    page = 1
    while True:
        url = f"{node.nodeURL}/api/posts/?page={page}&size=20"
        response = requests.get(url, auth=(node.username, node.password))
        if response.status_code != 200:
            break
            
        data = response.json()
        posts.extend(data.get('src', []))
        
        if len(data.get('src', [])) < 20:
            break
        page += 1
    return posts

# Comment synchronization
def fetch_post_comments(post_url, node):
    comments = []
    page = 1
    while True:
        url = f"{post_url}/comments/?page={page}&size=20"
        response = requests.get(url, auth=(node.username, node.password))
        if response.status_code != 200:
            break
            
        data = response.json()
        comments.extend(data.get('src', []))
        
        if len(data.get('src', [])) < 20:
            break
        page += 1
    return comments

# Like synchronization
def fetch_post_likes(post_url, node):
    likes = []
    page = 1
    while True:
        url = f"{post_url}/likes/?page={page}&size=50"
        response = requests.get(url, auth=(node.username, node.password))
        if response.status_code != 200:
            break
            
        data = response.json()
        likes.extend(data.get('src', []))
        
        if len(data.get('src', [])) < 50:
            break
        page += 1
    return likes

def get_node_data(node):
    try:
        # fetch and process users; idk if this works. Also, i only did the processing for users
        users = fetch_all_users(node)
        process_users(users, node)
        
        # Sync Posts
        posts = fetch_all_posts(node)
        
        for post_data in posts:
            post_uuid = extract_uuid_from_url(post_data['id'])
            post = Post.objects.filter(id=post_uuid).first()
            if post:
                # Comments
                comments = fetch_post_comments(post_data['id'], node)
                
                # Likes
                likes = fetch_post_likes(post_data['id'], node)
                
    except Exception as e:
        print(f"Error syncing node {node.nodeURL}: {str(e)}")
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
        url = f"{node.nodeURL}/api/authors/?page={page}&size=20"
        #response = requests.get(url, auth=(node.username, node.password))
        response = requests.get(url)
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
                'avatar_url': user.get('profileImage')
            }
        )

def fetch_author_posts(author_url, node):
    posts = []
    page = 1
    print(author_url)
    while True:
        url = f"{author_url}/posts/?page={page}&size=20"
        #response = requests.get(url, auth=(node.username, node.password))
        response = requests.get(url)
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
        #response = requests.get(url, auth=(node.username, node.password))
        response = requests.get(url)
        if response.status_code != 200:
            break
            
        data = response.json()
        comments.extend(data.get('src', []))
        if len(data.get('src', [])) < 20:
            break
        page += 1
    return comments

def process_comments(comments_data, post):
    for comment in comments_data:
        try:
            author = Authors.objects.get(id=comment['author']['id'])
        except Authors.DoesNotExist:
            continue
            
        Comment.objects.update_or_create(
            id=comment['id'],
            defaults={
                'author': author,
                'post': post,
                'comment': comment.get('comment'),
                'content_type': comment.get('contentType'),
                'published': comment.get('published')
            }
        )

# Like synchronization
def fetch_post_likes(post_url, node):
    likes = []
    page = 1
    while True:
        url = f"{post_url}/likes/?page={page}&size=50"
        #response = requests.get(url, auth=(node.username, node.password))
        response = requests.get(url)
        if response.status_code != 200:
            break
            
        data = response.json()
        likes.extend(data.get('src', []))
        
        if len(data.get('src', [])) < 50:
            break
        page += 1
    return likes

def fetch_all_posts(node):
    posts = []
    page = 1
    while True:
        url = f"{node.nodeURL}/api/posts/?page={page}&size=20"
        response = requests.get(url)
        if response.status_code != 200:
            break
            
        data = response.json()
        posts.extend(data.get('src', []))
        
        if len(data.get('src', [])) < 20:
            break
        page += 1
    return posts

def process_post(posts_data, node):
    for post in posts_data:
        user_uuid = extract_uuid_from_url(post['author'])
        if not user_uuid:
            continue
            
        author = Authors.objects.filter(row_id=user_uuid).first()
        if not author:
            continue
        
        post_uuid = extract_uuid_from_url(post['id'])
        if not post_uuid:
            continue
            
        Post.objects.update_or_create(
            id=post_uuid,
            defaults={
                'author': author,
                'content': post.get('content'),
                'content_type': post.get('contentType'),
                'published': post.get('published'),
                'visibility': post.get('visibility'),
                'is_deleted': post.get('isDeleted', False)
            }
        )

def process_likes(likes_data, post):
    for like in likes_data:
        try:
            author = Authors.objects.get(id=like['author']['id'])
        except Authors.DoesNotExist:
            continue
            
        Like.objects.update_or_create(
            id=like['id'],
            defaults={
                'author': author,
                'post': post,
                'published': like.get('published')
            }
        )

def get_node_data(node):
    try:
        # Sync users
        users = fetch_all_users(node)
        process_users(users, node)
        
        # Sync posts for each user
        for user_data in users:
            author_url = user_data['id']
            posts = fetch_author_posts(author_url, node)
            
            for post_data in posts:
                process_post(post_data, node)
                post = Post.objects.get(id=post_data['id'])
                
                # Sync comments
                comments = fetch_post_comments(post_data['id'], node)
                process_comments(comments, post)
                
                # Sync likes
                likes = fetch_post_likes(post_data['id'], node)
                process_likes(likes, post)
                
    except Exception as e:
        print(f"Error syncing node {node.nodeURL}: {str(e)}")
import requests
import uuid
from urllib.parse import urlparse
from accounts.models import Authors, Post, Comment, Like, FollowRequest, Follow
from .models import ExternalNode
from django.conf import settings

# ----------------
# Helper Functions
# ----------------
def extract_uuid_from_url(url):
    """
    Extract UUID v4 from URL path
    Example: http://example.com/api/authors/67b7b9bf-d2e4-4a22-8a57-4a087a8a9b1f/posts/67b7b9bf-alsdfkjghkljsdfhglkjsdf87a8a9b1f → 
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

def extract_second_uuid_from_url(url):
    """
    Extracts the 2nd UUID from URL path
    Example: http://example.com/api/authors/67b7b9bf-d2e4-4a22-8a57-4a087a8a9b1f/posts/67b7b9bf-alsdfkjghkljsdfhglkjsdf87a8a9b1f → 
    returns '67b7b9bf-alsdfkjghkljsdfhglkjsdf87a8a9b1f'
    """
    path_segments = urlparse(url).path.split('/')
    index = 0
    for segment in path_segments:
        try:
            uuid.UUID(segment)
            if index != 0:
                return segment
            else:
                index += 1
                continue
        except ValueError:
            continue
    return None

# ---------------
# Main Functions 
# ---------------
def fetch_all_users(node):
    """
    Upon successful registration with an External Node, 
    This function uses connected nodes api/authors, 
    and basically fetches all authors from the endpoint
    """
    users = []                                                                              
    page = 1                                                                                # Page for Traversal
    while True:                                                                             # Traverse Loop
        url = f"{node.nodeURL}/api/authors/?page={page}&size=20"
        response = requests.get(url)                                                        # Get data from endpoint
        if response.status_code != 200:                                                     # If no more data, exit loop
            break
            
        data = response.json()                                                              # Convert the data into a JSON
        #print(data)
        users.extend(data.get('authors', []))                                               # Append it to the Users List
        
        if len(data.get('authors', [])) < 20:                                               # Max 20 Users per page, if less, no need to check other pages
            break
        page += 1
    return users                                                                            # Return Users                                                             

def process_users(users_data, node):     
    """
    Uses the list provided (users_data), and creates the user instances in this list inside local DB
    """                   
    for user in users_data:                                                                 # Loop through the list
        print(user)
        user_uuid = extract_uuid_from_url(user['id'])                                       # Get the UUID of the user
        if not user_uuid:
            continue
        print(user.get('profileImage'))
        Authors.objects.update_or_create(                                                   # Create user in our current Database
            row_id=user_uuid,
            defaults={
                "id": user.get('id'),
                'host': user.get('host'),
                'username': user.get('displayName'),
                'displayName': user.get('displayName'),
                'github_username': user.get('github', '').split('/')[-1],
                'avatar_url': user.get('profileImage'),
                'local' : False
            }
        )

def fetch_author_posts(author_url, node):
    """
    Upon successful registration with an External Node, 
    This function uses connected nodes api/posts, 
    and basically fetches all posts from the endpoint
    """
    posts = []                                                                              # List of Posts
    page = 1                                                                                # Page for Traversal
    session = requests.Session()
    
    # Mimic browser headers
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)',
        'Referer': f'{node.nodeURL}/'
    }

    while True:                                                                             # Loop for Traversal
        url = f"{author_url}/posts/?page={page}&size=20"
        try:
            response = session.get(
                url,
                headers=headers
            )
            
            if response.status_code == 403:                                                 # Auth Failure
                print(f"Access forbidden. Trying without authentication...")
                response = session.get(url, headers=headers)
                
            if response.status_code != 200:                                                 # If no data received, break
                break

            data = response.json()                                                          # Convert data to JSON
            
            if isinstance(data, dict) and 'results' in data:                                
                page_posts = data['results']
                total_pages = data['total_pages']
            elif isinstance(data, dict) and 'src' in data:
                page_posts = data['src']
                total_pages = data['page_number']
            elif isinstance(data, list):
                page_posts = data
                total_pages = 1
            else:
                page_posts = []
                total_pages = 1
            posts.extend(page_posts)                                                        # Append Posts to List
            
            if page >= total_pages or len(page_posts) < 20:
                break
                
            page += 1
            
        except Exception as e:
            print(f"Error fetching posts: {str(e)}")
            break
            
    return posts

# Comment synchronization
def fetch_post_comments(post_url, node):
    """
    Upon successful registration with an External Node, 
    This function uses connected nodes api/posts/post_id/comments, 
    and basically fetches all comments from the endpoint
    """
    comments = []                                                                           # Comments List
    page = 1                                                                                # Page for Traversal
    while True:                                                                             # Traversal Loop
        url = f"{post_url}/comments/?page={page}&size=20"
        print(url)
        #response = requests.get(url, auth=(node.username, node.password))
        response = requests.get(url)
        if response.status_code != 200:                                                     # If no data, break
            break
            
        data = response.json()                                                              # Data to JSON

        if isinstance(data, dict) and 'results' in data:
            page_comments = data['results']
            total_pages = data['total_pages']
        elif isinstance(data, dict) and 'src' in data:
            page_comments = data['src']
            total_pages = data['page_number']
        elif isinstance(data, list):
            page_comments = data
            total_pages = 1
        else:
            page_comments = []
            total_pages = 1
        comments.extend(page_comments)                                                      # Append to List

        if page >= total_pages or len(page_comments) < 20:
            break
        page += 1
    return comments                                                                         # Return 

def process_comments(comments_data, post):
    for comment in comments_data:                                                           # For each comment in the list 
        if not isinstance(comment, dict):
            continue
        try:    
            # Get the Author of the Comment 
            author_data = comment.get('author')
            author_id = author_data.get('id')
            author = Authors.objects.get(id=author_id)

            # Get the Post that was commented on
            post_url = comment.get('post')
            post_uuid = extract_second_uuid_from_url(post_url)
            post = Post.objects.get(id=post_uuid)
            comment_uuid = extract_uuid_from_url(comment.get('id'))
            Comment.objects.update_or_create(
                id=comment_uuid,
                defaults={
                    'author': author,
                    'post': post,
                    'comment': comment.get('comment'),
                    'content_type': comment.get('contentType'),
                    'published': comment.get('published')
                }
            )
        except Exception as e:
            print(f"Error processing comment {comment}: {str(e)}")
            continue

# Like synchronization
def fetch_post_likes(post_url, node):
    likes = []
    page = 1
    while True:
        url = f"{post_url}/likes/?page={page}&size=20"
        print(url)
        response = requests.get(url)
        if response.status_code != 200:
            break
            
        data = response.json()
        print(data)
        if isinstance(data, dict) and 'results' in data:
            page_likes = data['results']
            total_pages = data['total_pages']
        elif isinstance(data, dict) and 'src' in data:
            page_likes = data['src']
            total_pages = data['page_number']
        elif isinstance(data, list):
            page_likes = data
            total_pages = 1
        else:
            page_likes = []
            total_pages = 1
        likes.extend(page_likes)

        if page >= total_pages or len(page_likes) < 20:
            break
        page += 1
    return likes

def process_post(posts_data, author_uuid, node):
    author = Authors.objects.filter(row_id=author_uuid).first()
    if not author:
        return

    post_id = posts_data.get('id', '')
    post_id = post_id.split("posts/")[1]
    post_uuid = uuid.UUID(post_id)

    image_fetch= posts_data.get('image')
    image_url = None
    image = None

    if image_fetch:
        if isinstance(image_fetch, str) and image_fetch.lower().startswith(('http://', 'https://')):
            image_url = image_fetch
        else:
            image = image_fetch

    Post.objects.update_or_create(
        id=post_uuid,
        defaults={
            'author': author,
            'title': posts_data.get('title'),
            'description': posts_data.get('description'),
            'content': posts_data.get('content'),
            'contentType': posts_data.get('contentType'),
            'image': image,
            'image_url': image_url,  
            'video': posts_data.get('video'),
            'published': posts_data.get('published'),
            'page': posts_data.get('page'),
            'visibility': posts_data.get('visibility'),
            'is_deleted': posts_data.get('isDeleted', False)
        }
    )

def process_likes(likes_data, post):
    for like in likes_data:
        if not isinstance(like, dict):
            continue
        try:
            # Get the Author of the Like
            author_data = like.get('author')
            author_id = author_data.get('id')
            author = Authors.objects.get(id=author_id)

            # Determine the Object Type
            object_url = like.get('object')
            if '/posts/' in object_url:
                liked_type = 'post'
            elif '/commented/' in object_url:
                liked_type = 'comment'
            object_uuid = extract_second_uuid_from_url(object_url)

            # Resolve Liked Object
            like_kwargs = {
                'author': author,
                'published': like.get('published')
            }

            if liked_type == 'post':
                try:
                    post = Post.objects.get(id=object_uuid)
                    like_kwargs['post'] = post
                except Post.DoesNotExist:
                    print("No Post")
                    continue
            elif liked_type == 'comment':
                try:
                    comment = Comment.objects.get(id=object_uuid)
                    like_kwargs['comment'] = comment
                except Comment.DoesNotExist:
                    print("No Comment")
                    continue
            
            # Get Like UUID
            like_uuid = extract_second_uuid_from_url(like.get('id'))

            Like.objects.update_or_create(
                id=like_uuid,
                defaults=like_kwargs
            )
        except Exception as e:
            print(f"Error processing like {like}: {str(e)}")
            continue

# def fetch_followers(author_url, node):
#     """
#     Fetch all followers of a given author from the external node during the initial sync
#     """
#     followers = []
#     page = 1
#     while True:
#         url = f"{author_url}/followers?page={page}&size=20"
#         response = requests.get(url)
#         print(f"Followers Response: {response.json()}")
#         if response.status_code != 200:
#             break
        
#         data = response.json()
#         print(f"Followers Data: {data}")
#         if isinstance(data, list):
#             page_followers = data
#         elif isinstance(data, dict) and 'followers' in data:
#             page_followers = data['followers']
#         else:
#             page_followers = []
#         followers.extend(page_followers)
#         print(f'\n\nRaw JSON Response: {data}\n\n')
#         print(f'\n\nfollowees List: {followers}\n\n')
#         if len(page_followers) < 20:
#             break
#         page += 1

#     return followers

# def fetch_followees(author_url, node):
#     """
#     Fetch all the authors that the given author follows upon initial sunc
#     """
#     followees = []
#     page = 1
#     while True:
#         url = f"{author_url}/followees?page={page}&size=20"
#         response = requests.get(url)
#         print(f"Followees Response: {response.json()}")
#         if response.status_code != 200:
#             break

#         data = response.json()
#         print(f"Followees Data: {data}")
#         if isinstance(data, list):
#             page_followees = data
#         elif isinstance(data, dict) and 'followees' in data:
#             page_followees = data['followees']
#         else:
#             page_followees = []

#         followees.extend(page_followees)
#         print(f'\n\nRaw JSON Response: {data}\n\n')
#         print(f'\n\nfollowees List: {followees}\n\n')
#         if len(page_followees) < 20:
#             break
#         page += 1

#     return followees

# def process_followers(followers_data, author):
#     """
#     Store fetched followers into the database upon initial sync
#     """
#     print("The code makes it to process_followers")
#     for follower in followers_data:
#         follower_id = extract_uuid_from_url(follower['id'])
#         print("Follower ID: ", follower_id)
#         if not follower_id:
#             continue

#         # first check if the follower author already exsits in db
#         follower_author = Authors.objects.filter(id=follower_id).first()

#         if not follower_author:
#             print(f"Warning: Author {follower_id} not found in database. Sync may be incomplete.")
#             continue
        
#         # if not follower_author: #create it it doesnt 
#         #     follower_author = Authors.objects.create(
#         #         id=follower_id,
#         #         host=follower.get('host'),
#         #         username=follower.get('displayName'),
#         #         displayName=follower.get('displayName'),
#         #         github_username=follower.get('github', '').split('/')[-1],
#         #         avatar_url=follower.get('profileImage'),
#         #         local=False
#         #     )

#         Follow.objects.update_or_create(
#             follower=follower_author,
#             following=author,
#             defaults={'accepted': True}
#         )

# def process_followees(followees_data, author):
#     """
#     Store fetched followees into the database upon initial sync
#     """
#     for followee in followees_data:
#         followee_id = extract_uuid_from_url(followee['id'])
#         if not followee_id:
#             continue

#         # first check if the followee author already exsits in db
#         followee_author = Authors.objects.filter(id=followee_id).first()

#         if not followee_author:
#             print(f"Warning: Author {followee_id} not found in database. Sync may be incomplete.")
#             continue

#         # if not followee_author: #create it it doesnt 
#         #     followee_author = Authors.objects.create(
#         #         id=followee_id,
#         #         host=followee.get('host'),
#         #         username=followee.get('displayName'),
#         #         displayName=followee.get('displayName'),
#         #         github_username=followee.get('github', '').split('/')[-1],
#         #         avatar_url=followee.get('profileImage'),
#         #         local=False
#         #     )

#         Follow.objects.update_or_create(
#             follower=author,
#             following=followee_author,
#             defaults={'accepted': True}
#         )

def get_node_data(node):
    try:
        # Sync users
        users = fetch_all_users(node)
        process_users(users, node)
        print("Users Synced")
        # Sync posts for each user
        for user_data in users:
            author_url = user_data['id']
            posts = fetch_author_posts(author_url, node)
            author_uuid = extract_uuid_from_url(author_url)
            print("Posts Synced")
            for post_data in posts:
                post = process_post(post_data, author_uuid, node)
                print("Post Done, Moving onto Comments")
                # Sync comments
                comments = fetch_post_comments(post_data['id'], node)
                print(comments)
                process_comments(comments, post)
                print("Comments Done, Moving onto Likes")
            
                # Sync likes
                likes = fetch_post_likes(post_data['id'], node)
                print(likes)
                process_likes(likes, post)
                print("Likes Done!")
            
            # #ensure there's no trailing slash in author_url (bug fix)

            # author_url_no_trailing_slash = author_url.rstrip('/')
            # print(f"Author URL: {author_url_no_trailing_slash}")
            
            # # Sync followers & followees
            # followers = fetch_followers(author_url_no_trailing_slash, node)
            # process_followers(followers, author_uuid)
            # print("Followers Synced")

            # followees = fetch_followees(author_url_no_trailing_slash, node)
            # process_followees(followees, author_uuid)
            # print("Followees Synced")

        print("Sync with Node successful")
        
    except Exception as e:
        print(f"Error syncing node {node.nodeURL}: {str(e)}")
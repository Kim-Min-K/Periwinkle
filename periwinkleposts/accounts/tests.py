from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase
from .models import Authors, Follow, FollowRequest, Post, Comment, Like
from .serializers import authorSerializer
import uuid
from urllib.parse import urlencode
from django.contrib.staticfiles.testing import LiveServerTestCase

# Create your tests here.
class FollowLiveServerTests(LiveServerTestCase):
    """ 
    This tests whether follow works on the frontend.
    """
    def setUp(self):
        host = self.live_server_url+"/api/"
        url = reverse("accounts:register")
        response = self.client.post(url, urlencode({
            'username': 'test_author_1', 
            'github_username':'test_author_1', 
            'host':host,
            'password1': 'my_password1', 
            'password2':'my_password1'
            }), content_type="application/x-www-form-urlencoded")
        self.assertEqual(response.status_code, 302) 

        response = self.client.post(url, urlencode({
            'username': 'test_author_2', 
            'github_username':'test_author_2', 
            'host':host,
            'password1': 'my_password2', 
            'password2':'my_password2'
            }), content_type="application/x-www-form-urlencoded")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(Authors.objects.all()), 2) 

        self.assertEqual(len(FollowRequest.objects.all()), 0)

        self.test_author_1 = Authors.objects.get(username="test_author_1")
        self.test_author_2 = Authors.objects.get(username="test_author_2")
        self.test_author_1.is_approved = 1
        self.test_author_2.is_approved = 1
        self.test_author_1.save()
        self.test_author_2.save()


    def test_send_follow_request(self):
        
        success = self.client.login(username="test_author_2", password="my_password2")
        self.assertEqual(success, True)

        url = reverse("accounts:sendFollowRequest", args=[self.test_author_1.id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(FollowRequest.objects.all()), 1)
    
    def test_accept_follow_request(self):
        print("\nTesting accept follow request live ...")
        self.assertEqual(len(Follow.objects.all()), 0)

        success = self.client.login(username="test_author_2", password="my_password2")
        self.assertEqual(success, True)

        url = reverse("accounts:sendFollowRequest", args=[self.test_author_1.id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(FollowRequest.objects.all()), 1)

        success = self.client.login(username="test_author_1", password="my_password1")
        self.assertEqual(success, True)

        url = reverse("accounts:acceptRequest", args=[self.test_author_1.row_id, self.test_author_2.id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(FollowRequest.objects.all()), 0)
        self.assertEqual(len(Follow.objects.all()), 1)
    
    def test_decline_follow_request(self):
        print("\nTesting decline follow request live ...")
        self.assertEqual(len(FollowRequest.objects.all()), 0)

        success = self.client.login(username="test_author_2", password="my_password2")
        self.assertEqual(success, True)

        url = reverse("accounts:sendFollowRequest", args=[self.test_author_1.id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(FollowRequest.objects.all()), 1)

        success = self.client.login(username="test_author_1", password="my_password1")
        self.assertEqual(success, True)

        url = reverse("accounts:declineRequest", args=[self.test_author_1.row_id, self.test_author_2.id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(FollowRequest.objects.all()), 0)
        self.assertEqual(len(Follow.objects.all()), 0)

    def test_unfollow(self):
        print("\nTesting unfollow live ...")

        success = self.client.login(username="test_author_2", password="my_password2")
        self.assertEqual(success, True)

        url = reverse("accounts:sendFollowRequest", args=[self.test_author_1.id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(FollowRequest.objects.all()), 1)

        success = self.client.login(username="test_author_1", password="my_password1")
        self.assertEqual(success, True)

        url = reverse("accounts:acceptRequest", args=[self.test_author_1.row_id, self.test_author_2.id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(FollowRequest.objects.all()), 0)
        self.assertEqual(len(Follow.objects.all()), 1)

        url = reverse("accounts:unfollow", args=[self.test_author_2.row_id, self.test_author_1.id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(Follow.objects.all()), 0)


    


class FollowAPITests(APITestCase):
    def test_get_followers(self):
        """
        Tests /api/authors/{author_serial}/followers endpoint with body.type == "followers"
        """
        test_author_1 = Authors.objects.create(username="test_author_1")
        test_author_2 = Authors.objects.create(username="test_author_2")
        test_author_3 = Authors.objects.create(username="test_author_3")

        Follow.objects.create(followee=test_author_1, follower=test_author_2)
        Follow.objects.create(followee=test_author_1, follower=test_author_3)

        url = reverse("api:getFollowers", args=[test_author_1.row_id])
        response = self.client.get(url)
        
        result = response.json()
        expected = {
            "type":"followers",
            "followers": [authorSerializer(test_author_2).data, authorSerializer(test_author_3).data]
        }

        self.assertEqual(result, expected)
        self.assertEqual(len(result["followers"]),2)
        self.assertEqual(response.status_code, 200)

    def test_send_follow_request(self):
        """
        Tests authors/<str:author_serial>/inbox endpoint with body.type == "follow"
        """

        # Create test authors
        test_author_1 = Authors.objects.create(username="test_author_1")
        test_author_2 = Authors.objects.create(username="test_author_2")

        # URL for sending the follow request
        url = reverse("api:followRequest", args=[test_author_1.row_id])

        # The request body for sending a follow request
        data = {
            "type": "follow",
            "actor": authorSerializer(test_author_2).data,  # The author sending the request
            "object": authorSerializer(test_author_1).data  # The author receiving the follow request
        }

        # Simulate sending a POST request
        response = self.client.post(url, data, format="json")

        # Assertions
        self.assertEqual(response.status_code, 200)  # Expecting HTTP 201 Created

        follow = FollowRequest.objects.filter(requestee=test_author_1, requester=test_author_2)
        self.assertTrue(follow.exists())


class CommentTest(APITestCase):
    def setUp(self):
        self.author = Authors.objects.create(username = 'test_author')
        self.post = Post.objects.create(author=self.author)
        Comment.objects.create(
            author=self.author, post=self.post, comment="Comment 1", content_type="text/plain"
        )
        Comment.objects.create(
            author=self.author, post=self.post, comment="Comment 2", content_type="text/plain"
        )
        self.author2 = Authors.objects.create(username = 'test_author2')
        Comment.objects.create(
            author=self.author2, post=self.post, comment="Comment 1 by author2", content_type="text/plain"
        )
        return super().setUp()
        
    
    #://service/api/authors/{AUTHOR_SERIAL}/commented POST
    def test_create_comment(self):
        url = reverse("api:createComment", kwargs={
            "author_serial": str(self.author.row_id),
        })
        comment_data = {
            "comment": "Comment 3",
            "contentType": "text/plain",
            "post": str(self.post.id),
            "author": {  
                "id": str(self.author.id),
                "username": self.author.username,
            }
        }
        response = self.client.post(url, comment_data, format="json")
        self.assertEqual(response.status_code, 201)  


    #://service/api/authors/{AUTHOR_SERIAL}/commented GET
    def test_get_author_comments(self):
        url = reverse("api:createComment", kwargs={"author_serial": str(self.author.row_id)})
        response = self.client.get(url, format="json")
        comments_data = response.data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(comments_data), 2)
        comments = []
        for comment in response.data:
            comments.append(comment['comment'])
        self.assertIn("Comment 1", comments)
        self.assertNotIn('Comment 1 by author2', comments) # ensure comment made by author2 won't be included
    
    # ://service/api/authors/{AUTHOR_SERIAL}/posts/{POST_SERIAL}/comments GET
    def test_get_post_comments(self):
        url = reverse("api:get_post_comments", kwargs={"author_serial": str(self.author.row_id), "post_serial": str(self.post.id)})
        response = self.client.get(url, format="json")
        comments_data = response.data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(comments_data), 3)

    def test_get_all_comments(self):
        url = reverse('api:commentList')
        response = self.client.get(url, format="json")
        comments_data = response.data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(comments_data), 3)

    def known_post_comments(self):
        url = reverse('api:known_post_comments')
        response = self.client.get(url, format="json")
        comments_data = response.data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(comments_data), 3)

class InboxTest(APITestCase):
    def setUp(self):
        self.author = Authors.objects.create(username="test_author")
        self.post = Post.objects.create(author=self.author)
        self.author2 = Authors.objects.create(username="test_author2")

    # ://service/api/authors/{AUTHOR_SERIAL}/inbox POST
    def test_post_comment_to_inbox(self):
        url = reverse("api:inbox", kwargs={"author_serial": str(self.author.row_id)})
        comment_data = {
            "type": "comment",
            "comment": "Inbox comment",
            "contentType": "text/plain",
            "post": f"http://localhost:8000/api/authors/{self.author.row_id}/posts/{self.post.id}",
            "author": {  
                "id": str(self.author2.id),  
                "username": self.author2.username,
            }
        }
        response = self.client.post(url, comment_data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Comment.objects.count(), 1)  
        self.assertEqual(Comment.objects.first().comment, "Inbox comment")



class LikeTest(APITestCase):
    def test_create_like(self):
        pass
    
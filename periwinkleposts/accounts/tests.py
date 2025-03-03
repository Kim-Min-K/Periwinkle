from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from .models import Authors, Follow, FollowRequest, Post, Comment, Like
from .serializers import authorSerializer
import uuid

# Create your tests here.
class FollowTests(APITestCase):
    def test_get_followers(self):
        """
        Tests /api/authors/{author_serial}/followers endpoint with body.type == "followers"
        """
        test_author_1 = Authors.objects.create(username="test_author_1")
        test_author_2 = Authors.objects.create(username="test_author_2")
        test_author_3 = Authors.objects.create(username="test_author_3")

        Follow.objects.create(followee=test_author_1, follower=test_author_2)
        Follow.objects.create(followee=test_author_1, follower=test_author_3)

        url = reverse("api:getFollowers", args=[test_author_1.row_id.hex])
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
        url = reverse("api:followRequest", args=[test_author_1.row_id.hex])

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
    def test_create_comment(self):
        test_author = Authors.objects.create(username = 'test_author')
        post = Post.objects.create()
        url = reverse("api:createComment", kwargs={
            "author_serial": str(test_author.id),
            "post_serial": str(post.id)
        })
        comment_data = {
            "comment": "This is a test comment",
            "contentType": "text/plain"
        }
        response = self.client.post(url, comment_data, format="json")
        self.assertEqual(response.status_code, status = 201)  
        self.assertEqual(Comment.objects.count(), 1)  
        self.assertEqual(Comment.objects.first().comment, "This is a test comment")


    
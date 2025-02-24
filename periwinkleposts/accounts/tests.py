from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from .models import Authors, Follow
from .serializers import authorSerializer


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

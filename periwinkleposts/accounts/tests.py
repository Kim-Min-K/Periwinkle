from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase
from .models import Authors, Follow, FollowRequest, Post, Comment, Like
from .serializers import authorSerializer
import uuid
from rest_framework import status
from rest_framework import permissions
from urllib.parse import urlencode
from django.contrib.staticfiles.testing import LiveServerTestCase
from urllib.parse import quote

from .seleniumtc import SeleniumTestCase
import time
from selenium.webdriver.common.by import By
from django.contrib.auth.hashers import make_password

# class AuthenticationFormTest(SeleniumTestCase):
#     def test_login(self):

#         dummy_username = "dummy_username"
#         dummy_password = "12345"

#         hashed_password = make_password(dummy_password, salt="Pq4u8aT8JZMTQGQclF93ch", hasher="pbkdf2_sha256")

#         # Create a user to login with
#         user = Authors.objects.create(
#             username=dummy_username, email="test@user.com", password=hashed_password, is_approved=1
#         )

#         print(Authors.objects.all())

#         # Go to the login page
#         self.driver.get(self.live_server_url + "/")


#         username = self.driver.find_element(By.ID, "username")

#         username.send_keys(dummy_username) 

#         password = self.driver.find_element(By.ID, "password")

#         password.send_keys(dummy_password)

#         time.sleep(0.5)

#         login = self.driver.find_element(By.TAG_NAME, "button")

#         login.click()

#         time.sleep(0.5)

#         self.assertEqual(self.driver.current_url, self.live_server_url + "/pages/home/")

class FollowUITests(SeleniumTestCase):
    
    def test_follow_functionality(self):

        # Register user 1
        self.dummy_username_1 = "username_1"
        self.dummy_github_1 = "dummy_github_1"
        self.dummy_password_1 = "114300Rom"

        self.driver.get(self.live_server_url + "/accounts/register/")

        username = self.driver.find_element(By.ID, "username")

        username.send_keys(self.dummy_username_1) 

        github_username = self.driver.find_element(By.ID, "github_username")

        github_username.send_keys(self.dummy_github_1)

        password1 = self.driver.find_element(By.ID, "password1")

        password1.send_keys(self.dummy_password_1)

        password2 = self.driver.find_element(By.ID, "password2")

        password2.send_keys(self.dummy_password_1)

        time.sleep(0.5)

        login = self.driver.find_element(By.TAG_NAME, "button")

        login.click()

        time.sleep(1)

        author = Authors.objects.get(username=self.dummy_username_1)
        author.is_approved=1
        author.save()

        time.sleep(0.5)

        # Register user 2
        self.dummy_username_2 = "username_2"
        self.dummy_github_2 = "dummy_github_2"
        self.dummy_password_2 = "114300Rom"

        self.driver.get(self.live_server_url + "/accounts/register/")

        username = self.driver.find_element(By.ID, "username")

        username.send_keys(self.dummy_username_2) 

        github_username = self.driver.find_element(By.ID, "github_username")

        github_username.send_keys(self.dummy_github_2)

        password1 = self.driver.find_element(By.ID, "password1")

        password1.send_keys(self.dummy_password_2)

        password2 = self.driver.find_element(By.ID, "password2")

        password2.send_keys(self.dummy_password_2)

        time.sleep(0.5)

        login = self.driver.find_element(By.TAG_NAME, "button")

        login.click()

        time.sleep(1)

        author = Authors.objects.get(username=self.dummy_username_2)
        author.is_approved=1
        author.save()

        time.sleep(0.5)

        # Login as user 1

        self.driver.get(self.live_server_url + "/")


        username = self.driver.find_element(By.ID, "username")

        username.send_keys(self.dummy_username_1) 

        time.sleep(0.5)

        password = self.driver.find_element(By.ID, "password")

        password.send_keys(self.dummy_password_1)


        time.sleep(0.5)

        login = self.driver.find_element(By.TAG_NAME, "button")

        login.click()

        time.sleep(1)

        self.assertEqual(self.driver.current_url, self.live_server_url + "/pages/home/")

        profile = self.driver.find_element(By.XPATH, "/html/body/nav/div/div/a[2]")

        profile.click()

        time.sleep(0.5)

        suggestions = self.driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/div/div[3]/button")
        suggestions.click()

        follow = self.driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/div/div[3]/div/ul/li/form/button")
        follow.click()

        time.sleep(0.5)

        # Check sent requests after following somebody
        sent = self.driver.find_elements(By.XPATH, "/html/body/div/div/div/div[2]/div/div[2]/ul/li/a")
        self.assertEqual(len(sent), 1, "Sent Requests does not have an item.")

        time.sleep(0.5)

        # Login as user 2

        self.driver.get(self.live_server_url + "/")

        username = self.driver.find_element(By.ID, "username")

        username.send_keys(self.dummy_username_2) 

        password = self.driver.find_element(By.ID, "password")

        password.send_keys(self.dummy_password_2)

        login = self.driver.find_element(By.TAG_NAME, "button")

        login.click()

        time.sleep(0.5)

        self.assertEqual(self.driver.current_url, self.live_server_url + "/pages/home/")

        profile = self.driver.find_element(By.XPATH, "/html/body/nav/div/div/a[2]")

        profile.click()

        time.sleep(0.5)

        unfollow = self.driver.find_elements(By.XPATH, "/html/body/div/div/div/div[2]/div/div[6]/div/ul/li/form/button")
        self.assertEqual(len(unfollow), 0, "followees is not 0.")

        requests = self.driver.find_elements(By.XPATH, "/html/body/div/div/div/div[2]/div/div[1]/ul/li/div/button[1]/a")
        self.assertEqual(len(requests), 1, "Receive request is not 1.")

        followers = self.driver.find_elements(By.XPATH, "/html/body/div/div/div/div[2]/div/div[5]/div/ul/li/a")
        self.assertEqual(len(followers), 0, "Followers is not 0.")

        accept = self.driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/div/div[1]/ul/li/div/button[1]/a")
        accept.click()

        time.sleep(0.5)

        requests = self.driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/div/div[1]/ul/li")
        self.assertEqual(requests.text, "No received requests", "Receive request is not 0.")

        # Check Followers after following somebody
        followers = self.driver.find_elements(By.XPATH, "/html/body/div/div/div/div[2]/div/div[5]/div/ul/li/a")
        self.assertEqual(len(followers), 1, "Followers is empty after following somebody.")


        suggestions = self.driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/div/div[3]/button")
        suggestions.click()

        time.sleep(0.5)

        profile_link = self.driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/div/div[3]/div/ul/li[1]/span/a")
        profile_link.click()

        time.sleep(0.5)

        follow = self.driver.find_element(By.XPATH, "/html/body/div/div/div/div[1]/div[1]/div[2]/div[1]/form/button")
        follow.click()

        time.sleep(0.5)

        # Check sent requests after following user 1 using profile page
        sent = self.driver.find_elements(By.XPATH, "/html/body/div/div/div/div[2]/div/div[2]/ul/li/a")
        self.assertEqual(len(sent), 1, "Sent Requests is empty after following using profile page.")

        # Login again user 1

        self.driver.get(self.live_server_url + "/")


        username = self.driver.find_element(By.ID, "username")

        username.send_keys(self.dummy_username_1) 

        time.sleep(0.5)

        password = self.driver.find_element(By.ID, "password")

        password.send_keys(self.dummy_password_1)


        time.sleep(0.5)

        login = self.driver.find_element(By.TAG_NAME, "button")

        login.click()

        time.sleep(1)

        self.assertEqual(self.driver.current_url, self.live_server_url + "/pages/home/")

        profile = self.driver.find_element(By.XPATH, "/html/body/nav/div/div/a[2]")

        profile.click()

        time.sleep(0.5)

        # Accept request from user 2

        requests = self.driver.find_elements(By.XPATH, "/html/body/div/div/div/div[2]/div/div[1]/ul/li/div/button[1]/a")
        self.assertEqual(len(requests), 1, "Receive request is not 1.")

        followers = self.driver.find_elements(By.XPATH, "/html/body/div/div/div/div[2]/div/div[5]/div/ul/li/a")
        self.assertEqual(len(followers), 0, "Followers is not 0.")

        accept = self.driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/div/div[1]/ul/li/div/button[1]/a")
        accept.click()

        time.sleep(0.5)


        # Check if they move to friends

        friends = self.driver.find_elements(By.XPATH, "/html/body/div/div/div/div[2]/div/div[4]/div/ul/li/form/button")
        self.assertEqual(len(friends), 1, "Did not move to friend after following.")

        friends_toggle = self.driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/div/div[4]/button")
        friends_toggle.click()

        time.sleep(0.5)

        unfriend = self.driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/div/div[4]/div/ul/li/form/button")
        unfriend.click()

        time.sleep(0.5)

        # Check suggestions after unfriending
        suggestions = self.driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/div/div[3]/button")
        suggestions.click()

        time.sleep(0.5)

        follow = self.driver.find_elements(By.XPATH, "/html/body/div/div/div/div[2]/div/div[3]/div/ul/li/form/button")
        self.assertEqual(len(follow), 1, "Suggestions doesn't have an item after unfriending.")

        follow = self.driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/div/div[3]/div/ul/li/form/button")
        follow.click()

        time.sleep(0.5)


        # Login again as user 2
        self.driver.get(self.live_server_url + "/")

        username = self.driver.find_element(By.ID, "username")

        username.send_keys(self.dummy_username_2) 

        password = self.driver.find_element(By.ID, "password")

        password.send_keys(self.dummy_password_2)

        login = self.driver.find_element(By.TAG_NAME, "button")

        login.click()

        time.sleep(0.5)

        profile = self.driver.find_element(By.XPATH, "/html/body/nav/div/div/a[2]")

        profile.click()

        time.sleep(0.5)


        # Accept request from user 1
        requests = self.driver.find_elements(By.XPATH, "/html/body/div/div/div/div[2]/div/div[1]/ul/li/div/button[1]/a")
        self.assertEqual(len(requests), 1, "Received request does not have an item.")

        accept = self.driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/div/div[1]/ul/li/div/button[1]/a")
        accept.click()

        time.sleep(0.5)


        # Unfriend using profile page
        friends_toggle = self.driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/div/div[4]/button")
        friends_toggle.click()

        time.sleep(0.5)

        friend_profile_link = self.driver.find_element(By.XPATH,"/html/body/div/div/div/div[2]/div/div[4]/div/ul/li/a")
        friend_profile_link.click()

        time.sleep(0.5)

        unfriend = self.driver.find_element(By.XPATH,"/html/body/div/div/div/div[1]/div[1]/div[2]/div[1]/form/button")
        unfriend.click()

        time.sleep(0.5)

        followees = self.driver.find_elements(By.XPATH, "/html/body/div/div/div/div[2]/div/div[6]/div/ul/li/form/button")
        self.assertEqual(len(followees), 0, "Followees is not 0 after unfriending.")

        suggestions = self.driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/div/div[3]/button")
        suggestions.click()
        time.sleep(0.5)

        follow = self.driver.find_elements(By.XPATH, "/html/body/div/div/div/div[2]/div/div[3]/div/ul/li/form/button")
        self.assertEqual(len(follow), 1, "Suggestions doesn't have an item after unfriending.")

        # Login again as user 1
        self.driver.get(self.live_server_url + "/")


        username = self.driver.find_element(By.ID, "username")

        username.send_keys(self.dummy_username_1) 

        time.sleep(0.5)

        password = self.driver.find_element(By.ID, "password")

        password.send_keys(self.dummy_password_1)


        time.sleep(0.5)

        login = self.driver.find_element(By.TAG_NAME, "button")

        login.click()
        time.sleep(0.5)

        time.sleep(1)

        self.assertEqual(self.driver.current_url, self.live_server_url + "/pages/home/")

        profile = self.driver.find_element(By.XPATH, "/html/body/nav/div/div/a[2]")

        profile.click()

        time.sleep(0.5)

        # Unfollow user 2
        followees_toggle = self.driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/div/div[6]/button")

        followees_toggle.click()

        time.sleep(0.5)

        unfollow = self.driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/div/div[6]/div/ul/li/form/button")

        unfollow.click()

        time.sleep(0.5)

        suggestions = self.driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/div/div[3]/button")
        suggestions.click()
        time.sleep(0.5)
        follow = self.driver.find_elements(By.XPATH, "/html/body/div/div/div/div[2]/div/div[3]/div/ul/li/form/button")
        
        # Check if they move to suggestions
        self.assertEqual(len(follow), 1, "Suggestions doesn't have an item after unfollowing.")



class IsOwnerOrPublic(permissions.BasePermission):
    """
    Custom permission:
    - Allow read access for public posts to everyone
    - Allow full access to post owner
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return obj.visibility == 'PUBLIC'
        return obj.author == request.user

class IsLocalAuthor(permissions.BasePermission):
    """
    Simplified local author check for testing:
    - Treat any authenticated user as local
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

# Create your tests here.
class FollowLiveServerTests(LiveServerTestCase):
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

        url = reverse("accounts:sendFollowRequest", args=[self.test_author_1.row_id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(FollowRequest.objects.all()), 1)
    
    def test_accept_follow_request(self):
        print("\nTesting accept follow request live ...")
        self.assertEqual(len(Follow.objects.all()), 0)

        success = self.client.login(username="test_author_2", password="my_password2")
        self.assertEqual(success, True)

        url = reverse("accounts:sendFollowRequest", args=[self.test_author_1.row_id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(FollowRequest.objects.all()), 1)

        success = self.client.login(username="test_author_1", password="my_password1")
        self.assertEqual(success, True)

        url = reverse("accounts:acceptRequest", args=[self.test_author_1.row_id, self.test_author_2.row_id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(FollowRequest.objects.all()), 0)
        self.assertEqual(len(Follow.objects.all()), 1)
    
    def test_decline_follow_request(self):
        print("\nTesting decline follow request live ...")
        self.assertEqual(len(FollowRequest.objects.all()), 0)

        success = self.client.login(username="test_author_2", password="my_password2")
        self.assertEqual(success, True)

        url = reverse("accounts:sendFollowRequest", args=[self.test_author_1.row_id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(FollowRequest.objects.all()), 1)

        success = self.client.login(username="test_author_1", password="my_password1")
        self.assertEqual(success, True)

        url = reverse("accounts:declineRequest", args=[self.test_author_1.row_id, self.test_author_2.row_id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(FollowRequest.objects.all()), 0)
        self.assertEqual(len(Follow.objects.all()), 0)

    def test_unfollow(self):
        print("\nTesting unfollow live ...")

        success = self.client.login(username="test_author_2", password="my_password2")
        self.assertEqual(success, True)

        url = reverse("accounts:sendFollowRequest", args=[self.test_author_1.row_id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(FollowRequest.objects.all()), 1)

        success = self.client.login(username="test_author_1", password="my_password1")
        self.assertEqual(success, True)

        url = reverse("accounts:acceptRequest", args=[self.test_author_1.row_id, self.test_author_2.row_id])

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
        self.maxDiff=None
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
            "authors": [authorSerializer(test_author_2).data, authorSerializer(test_author_3).data]
        }

        self.assertEqual(len(result["authors"]),2)
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
    
    def test_get_followees(self):
        self.maxDiff = None
        test_author_1 = Authors.objects.create(username="test_author_1")
        test_author_2 = Authors.objects.create(username="test_author_2")
        test_author_3 = Authors.objects.create(username="test_author_3")

        Follow.objects.create(followee=test_author_2, follower=test_author_1)
        Follow.objects.create(followee=test_author_3, follower=test_author_1)

        url = reverse("api:getFollowees", args=[test_author_1.row_id])
        response = self.client.get(url)
        
        result = response.json()
        expected = {
            "type":"followees",
            "followees": [authorSerializer(test_author_3).data, authorSerializer(test_author_2).data]
        }

        self.assertEqual(len(result["followees"]),2)
        self.assertEqual(response.status_code, 200)
        

class FollowRequestAPITests(APITestCase):
    def setUp(self):
        # Create test authors
        self.test_author_1 = Authors.objects.create(username="test_author_1")
        self.test_author_2 = Authors.objects.create(username="test_author_2")

        # URL for sending the follow request
        url = reverse("api:followRequest", args=[self.test_author_1.row_id])

        # The request body for sending a follow request
        data = {
            "type": "follow",
            "actor": authorSerializer(self.test_author_2).data,  # The author sending the request
            "object": authorSerializer(self.test_author_1).data  # The author receiving the follow request
        }

        # Simulate sending a POST request
        response = self.client.post(url, data, format="json")

        # Assertions
        self.assertEqual(response.status_code, 200)  # Expecting HTTP 201 Created

        follow = FollowRequest.objects.filter(requestee=self.test_author_1, requester=self.test_author_2)
        self.assertTrue(follow.exists())

    def test_get_follow_requests(self):
        url = reverse("api:getFollowRequestIn", args=[self.test_author_1.row_id])
        
        response = self.client.get(url)

        result = response.json()
        expected = {
            "type": "incoming-follow-requests",
            "authors": [authorSerializer(self.test_author_2).data]
        }

        self.assertEqual(result, expected)
        self.assertEqual(len(result["authors"]),1)
        self.assertEqual(response.status_code, 200)
    
    def test_get_outgoing_follow_requests(self):
        self.maxDiff = None
        url = reverse("api:getFollowRequestOut", args=[self.test_author_2.row_id])
        
        response = self.client.get(url)

        result = response.json()
        expected = {
            "type": "outgoing-follow-requests",
            "authors": [authorSerializer(self.test_author_1).data]
        }

        self.assertEqual(result, expected)
        self.assertEqual(len(result["authors"]),1)
        self.assertEqual(response.status_code, 200)
    
    def test_get_request_suggestions(self):
        self.maxDiff = None
        url = reverse("api:getRequestSuggestions", args=[self.test_author_2.row_id])
        
        response = self.client.get(url)

        result = response.json()
        expected = {
            "type": "request-suggestions",
            "authors": []
        }

        self.assertEqual(result, expected)
        self.assertEqual(len(result["authors"]),0)
        self.assertEqual(response.status_code, 200)

class FriendsAPITests(APITestCase):
    def test_get_friends(self):
        test_author_1 = Authors.objects.create(username="test_author_1")
        test_author_2 = Authors.objects.create(username="test_author_2")
        test_author_3 = Authors.objects.create(username="test_author_3")

        url = reverse("api:getFriends", args=[test_author_1.row_id])
        response = self.client.get(url)
        result = response.json()
        expected = {
            "type":"friends",
            "authors": []
        }
        self.assertEqual(result, expected)

        Follow.objects.create(followee=test_author_2, follower=test_author_1)
        Follow.objects.create(followee=test_author_1, follower=test_author_2)

        url = reverse("api:getFriends", args=[test_author_1.row_id])
        response = self.client.get(url)
        
        result = response.json()
        expected = {
            "type":"friends",
            "authors": [authorSerializer(test_author_2).data]
        }

        self.assertEqual(result, expected)
        self.assertEqual(len(result["authors"]),1)
        self.assertEqual(response.status_code, 200)


class CommentTest(APITestCase):
    def setUp(self):
        self.author = Authors.objects.create(username = 'test_author')
        self.post = Post.objects.create(author=self.author)
        self.post2 = Post.objects.create(author= self.author)
        self.comment1 = Comment.objects.create(
            author=self.author, post=self.post, comment="Comment 1", content_type="text/plain"
        )
        Comment.objects.create(
            author=self.author, post=self.post, comment="Comment 2", content_type="text/plain"
        )
        self.author2 = Authors.objects.create(username = 'test_author2')
        Comment.objects.create(
            author=self.author2, post=self.post, comment="Comment 1 by author2", content_type="text/plain"
        )
        Comment.objects.create(
            author=self.author, post=self.post2, comment="author Comment on post2", content_type="text/plain"
        )
        return super().setUp()
    #------------------Test for comments----------------
    # ://service/api/authors/{AUTHOR_SERIAL}/posts/{POST_SERIAL}/comments GET
    def test_get_post_comments(self):
        url = reverse("api:get_post_comments", kwargs={"author_serial": str(self.author.row_id), "post_serial": str(self.post.id)})
        response = self.client.get(url, format="json")
        comments_data = response.data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(comments_data), 3)

    # shows all comments GET
    def test_get_all_comments(self):
        url = reverse('api:commentList')
        response = self.client.get(url, format="json")
        comments_data = response.data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(comments_data), 4)

    # ://service/api/posts/{POST_FQID}/comments GET
    def test_known_post_comments(self):
        post_fqid = f"http://localhost:8000/api/authors/{self.author.row_id}/posts/{self.post.id}"
        encoded_post_fqid = quote(post_fqid, safe='') 
        # URLs contain special characters (/, :), which Django's URL routing does not parse correctly.
        url = reverse('api:known_post_comments', kwargs={'post_fqid':encoded_post_fqid})
        response = self.client.get(url, format="json")
        comments_data = response.data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(comments_data), 3)

    # ://service/api/authors/{AUTHOR_SERIAL}/post/{POST_SERIAL}/comment/{REMOTE_COMMENT_FQID} GET
    def test_get_comment(self):
        url = reverse(
            'api:get_comment',  
            kwargs={
                "author_serial": str(self.author.row_id),
                "post_serial": str(self.post.id),
                "remote_comment_fqid": str(self.comment1.id)
            },
        )
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["comment"], "Comment 1")

    #------------------Test for commented----------------
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
        self.assertEqual(len(comments_data), 3)
        comments = []
        for comment in response.data:
            comments.append(comment['comment'])
        self.assertIn("Comment 1", comments)
        self.assertNotIn('Comment 1 by author2', comments) # ensure comment made by author2 won't be included
    
    
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

class AuthorViewSetTests(APITestCase):
    def setUp(self):
        for i in range(15):
            Authors.objects.create(
                username=f"author_{i}",
                github_username=f"github_{i}",
                host="http://testserver",
                avatar_url=f"http://example.com/avatar_{i}.jpg"
            )

    # Retrieve single author tests
    def test_author(self):
        author = Authors.objects.first()
        url = reverse('api:getAuthor', args=[author.row_id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['id'],
            f"http://testserver/api/authors/{author.row_id}"  # Updated URL format
        )

    def test_404(self):
        invalid_uuid = uuid.uuid4()
        url = reverse('api:getAuthor', args=[invalid_uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # List authors tests
    def test_authors_dpag(self):
        url = reverse('api:getAuthors')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['type'], 'authors')
        self.assertEqual(len(response.data['authors']), 10)
        first_author = Authors.objects.order_by('id').first()
        self.assertEqual(
            response.data['authors'][0]['displayName'],
            first_author.username
        )

    def test_authors_cpag(self):
        url = reverse('api:getAuthors')
        response = self.client.get(url, {'page': 2, 'size': 5})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['authors']), 5)
        # first item on page 2 is 6th author
        sixth_author = Authors.objects.order_by('id')[5]
        self.assertEqual(
            response.data['authors'][0]['displayName'],
            sixth_author.username
        )

    def test_authors_ipag(self):
        """Test invalid pagination parameters"""
        url = reverse('api:getAuthors')
        response = self.client.get(url, {'page': 'invalid', 'size': 'wrong'})
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid page or size parameters')

    def test_authors_empty(self):
        """Test requesting non-existent page returns empty list"""
        url = reverse('api:getAuthors')
        response = self.client.get(url, {'page': 3, 'size': 10})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            "type": "authors",
            "authors": []
        })
        
class PostAPITests(APITestCase):
    def setUp(self):
        # Create test authors
        self.owner = Authors.objects.create_user(
            username="owner",
            password="ownerpass"
        )
        self.anon = Authors.objects.create_user(
            username="anon",
            password="anonpass"
        )
        
        self.public_post = Post.objects.create(
            author=self.owner,
            title="Public Post",
            content="Public content",
            contentType="text/plain",
            visibility="PUBLIC"
        )
        
        self.private_post = Post.objects.create(
            author=self.owner,
            title="Private Post",
            content="Private content",
            contentType="text/plain",
            visibility="FRIENDS" 
        )

    def test_create_post_success(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse('api:author-posts', args=[self.owner.row_id])
        data = {
            "title": "Manual Test Post",
            "description": "Testing post creation",
            "content": "test content",
            "contentType": "text/plain",
            "visibility": "PUBLIC"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_owner(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse('api:post-detail', args=[self.owner.row_id, self.public_post.id])
        data = {
            "title": "Updated Title",
            "description": "Updated description", 
            "content": "Updated content",
            "contentType": "text/plain",
            "visibility": "PUBLIC"
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.public_post.refresh_from_db()
        self.assertEqual(self.public_post.title, "Updated Title")

    def test_update_anon(self):
        self.client.force_authenticate(user=self.anon)
        url = reverse('api:post-detail', args=[self.owner.row_id, self.public_post.id])
        data = {"title": "you shouldnt be able to see this"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_owner(self):
        """Owner can soft-delete their post"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('api:post-detail', args=[self.owner.row_id, self.public_post.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(Post.objects.get(id=self.public_post.id).is_deleted)

    def test_delete_anon(self):
        """anon cannot delete post"""
        self.client.force_authenticate(user=self.anon)
        url = reverse('api:post-detail', args=[self.owner.row_id, self.public_post.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

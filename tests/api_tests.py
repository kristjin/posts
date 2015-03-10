import unittest
import os
import json
from urlparse import urlparse

# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "posts.config.TestingConfig"

from posts import app
from posts import models
from posts.database import Base, engine, session

class TestAPI(unittest.TestCase):
    """ Tests for the posts API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

    def testGetPosts(self):
        """ Getting posts from a populated database """
        # Create a couple of sample posts
        postA = models.Post(title="Example Post A", body="Just a test")
        postB = models.Post(title="Example Post B", body="Still a test")
        # Add them to the session and commit
        session.add_all([postA, postB])
        session.commit()
        # Go to the page and get the response from the server, store it here
        response = self.client.get("/api/posts")
        # Was the request to the endpoint successful?
        self.assertEqual(response.status_code, 200)
        # Did the request return a JSON object?
        self.assertEqual(response.mimetype, "application/json")
        # Decode the data using json.loads
        data = json.loads(response.data)
        # Verify that two posts have been returned
        self.assertEqual(len(data), 2)
        # Verify the contents of both posts as correct
        postA = data[0]
        self.assertEqual(postA["title"], "Example Post A")
        self.assertEqual(postA["body"], "Just a test")
        postB = data[1]
        self.assertEqual(postB["title"], "Example Post B")
        self.assertEqual(postB["body"], "Still a test")

    def testGetEmptyPosts(self):
        """ Getting posts from an empty database """
        # Go to the page and get the response from the server, store it here
        response = self.client.get("/api/posts")
        # Was the request to the endpoint successful?
        self.assertEqual(response.status_code, 200)
        # Did the request return a JSON object?
        self.assertEqual(response.mimetype, "application/json")
        # Decode the data using json.loads
        data = json.loads(response.data)
        # Is the JSON empty (because this tests an empty db)
        self.assertEqual(data, [])

    def tearDown(self):
        """ Test teardown """
        session.close()
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)

if __name__ == "__main__":
    unittest.main()

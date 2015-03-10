import unittest
import os
import json
from urlparse import urlparse

# Configure our app to use the testing database
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

    def testInvalidData(self):
        """ Posting a post with an invalid body """
        data = {
            "title": "Example Post",
            "body": 32
        }

        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 422)

        data = json.loads(response.data)
        self.assertEqual(data["message"], "32 is not of type 'string'")

    def testMissingData(self):
        """ Posting a post with a missing body """
        data = {
            "title": "Example Post",
        }

        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 422)

        data = json.loads(response.data)
        self.assertEqual(data["message"], "'body' is a required property")

    def testUnsupportedMimetype(self):
        """ Test Sending Unsupported Mime Type """
        data = "<xml></xml>"
        response = self.client.post("/api/posts",
                                    data=json.dumps(data),
                                    content_type="application/xml",
                                    headers=[("Accept", "application/json")],
                                    )

        self.assertEqual(response.status_code, 415)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(data["message"],
                         "Request must contain application/json data")

    def testPostPost(self):
        """ Posting a new post """
        # Compile post data into a dictionary for easy conversion to JSON
        data = {
            "title": "Example Post",
            "body": "Just a test"
        }

        # Collect the response from the endpoint
        # use json.dumps to convert dict > JSON
        # use content_type to indicate the type of content in data
        response = self.client.post("/api/posts",
                                    data=json.dumps(data),
                                    content_type="application/json",
                                    headers=[("Accept", "application/json")],
                                    )

        # Verify request to endpoint was successful using 201 created
        self.assertEqual(response.status_code, 201)
        # Verify that the response is JSON type
        self.assertEqual(response.mimetype, "application/json")
        # Verify the endpoint is setting the correct Location header
        # This should be the link to the new post
        self.assertEqual(urlparse(response.headers.get("Location")).path,
                         "/api/posts/1")
        # Decode the response with json.loads
        data = json.loads(response.data)
        # Validate the id, title and body
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["title"], "Example Post")
        self.assertEqual(data["body"], "Just a test")
        # Query DB to validate status
        posts = session.query(models.Post).all()
        # Verify only one item in DB
        self.assertEqual(len(posts), 1)
        # Isolate the first post in the list received
        post = posts[0]
        # Validate the content of the item retrieved from the DB
        self.assertEqual(post.title, "Example Post")
        self.assertEqual(post.body, "Just a test")



    def testGetPostsWithTitle(self):
        """ Filtering posts by title """
        postA = models.Post(title="Post with bells",
                            body="Just a test",
                            )
        postB = models.Post(title="Post with whistles",
                            body="Still a test",
                            )
        postC = models.Post(title="Post with bells and whistles",
                            body="Another test",
                            )

        session.add_all([postA, postB, postC])
        session.commit()

        response = self.client.get("/api/posts?title_like=whistles",
                                   headers=[("Accept", "application/json")],
                                   )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        posts = json.loads(response.data)
        self.assertEqual(len(posts), 2)

        post = posts[0]
        self.assertEqual(post["title"], "Post with whistles")
        self.assertEqual(post["body"], "Still a test")

        post = posts[1]
        self.assertEqual(post["title"], "Post with bells and whistles")
        self.assertEqual(post["body"], "Another test")

    def testGetPostsWithTitleandBody(self):
        """ Filtering posts by title """
        postA = models.Post(title="Post with bells",
                            body="No whistles",
                            )
        postB = models.Post(title="Post with whistles",
                            body="No bells",
                            )
        postC = models.Post(title="Post with bells and whistles",
                            body="Both bells and whistles",
                            )

        session.add_all([postA, postB, postC])
        session.commit()

        response = self.client.get("/api/posts?title_like=whistles&body_like=bells",
                                   headers=[("Accept", "application/json")],
                                   )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        posts = json.loads(response.data)
        self.assertEqual(len(posts), 2)

        post = posts[0]
        self.assertEqual(post["title"], "Post with whistles")
        self.assertEqual(post["body"], "No bells")

        post = posts[1]
        self.assertEqual(post["title"], "Post with bells and whistles")
        self.assertEqual(post["body"], "Both bells and whistles")

    def testGetPosts(self):
        """ Getting posts from a populated database """
        # Create a couple of sample posts
        postA = models.Post(title="Example Post A", body="Just a test")
        postB = models.Post(title="Example Post B", body="Still a test")
        # Add them to the session and commit
        session.add_all([postA, postB])
        session.commit()
        # Go to the page and get the response from the server, store it here
        response = self.client.get("/api/posts",
                                   headers=[("Accept", "application/json")],
                                   )
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
        response = self.client.get("/api/posts",
                                   headers=[("Accept", "application/json")],
                                   )
        # Was the request to the endpoint successful?
        self.assertEqual(response.status_code, 200)
        # Did the request return a JSON object?
        self.assertEqual(response.mimetype, "application/json")
        # Decode the data using json.loads
        data = json.loads(response.data)
        # Is the JSON empty (because this tests an empty db)
        self.assertEqual(data, [])

    def testGetPost(self):
        """ Getting a single post from a populated database """
        postA = models.Post(title="Example Post A", body="Just a test")
        postB = models.Post(title="Example Post B", body="Still a test")

        session.add_all([postA, postB])
        session.commit()

        response = self.client.get("/api/posts/{}".format(postB.id),
                                   headers=[("Accept", "application/json")],
                                   )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        post = json.loads(response.data)
        self.assertEqual(post["title"], "Example Post B")
        self.assertEqual(post["body"], "Still a test")

    def testDeletePost(self):
        """ Deleting a single post from a populated database """
        postA = models.Post(title="Example Post A", body="Just a test")
        postB = models.Post(title="Example Post B", body="Still a test")

        session.add_all([postA, postB])
        session.commit()

        response = self.client.delete("/api/posts/{}".format(postB.id),
                                      headers=[("Accept", "application/json")],
                                      )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(data["message"], "Deleted post with id {}".format(postB.id))

    def testDeleteNonExistentPost(self):
        """ Trying to Delete a non-existent Post """
        response = self.client.delete("/api/posts/1",
                                      headers=[("Accept", "application/json")],
                                      )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(data["message"], "Could not find post with id 1")

    def testGetNonExistentPost(self):
        """ Getting a single post which doesn't exist """
        response = self.client.get("/api/posts/1",
                                   headers=[("Accept", "application/json")],
                                   )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(data["message"], "Could not find post with id 1")

    def testUnsupportedAcceptHeader(self):
        response = self.client.get("/api/posts",
                                   headers=[("Accept", "application/xml")],
                                   )

        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(data["message"],
                         "Request must accept application/json data")

    def tearDown(self):
        """ Test teardown """
        session.close()
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)

if __name__ == "__main__":
    unittest.main()

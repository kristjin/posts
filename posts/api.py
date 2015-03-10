import json

from flask import request, Response, url_for
from jsonschema import validate, ValidationError

import models
import decorators
from posts import app
from database import session

@app.route("/api/posts", methods=["GET"])
def posts_get():
    """ Get a list of posts """
    # Obtain the posts from the database
    posts = session.query(models.Post).all()
    # Convert the data to JSON format
    data = json.dumps([post.as_dictionary() for post in posts])
    # Return a 200 status and the data
    return Response(data, 200, mimetype="application/json")
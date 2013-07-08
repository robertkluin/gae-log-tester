
import itertools
import logging
import random
import string

import webapp2

from jinja2 import Environment
from jinja2.loaders import FileSystemLoader

from google.appengine.api import logservice
from google.appengine.api import taskqueue

from google.appengine.ext import db


class Entity(db.Model):
    pass


class ConfigHandler(webapp2.RequestHandler):
    """Configure the test case."""
    def get(self):

        jinja_env = Environment(loader=FileSystemLoader('templates'))

        template = jinja_env.get_template('config.jinja')
        self.response.out.write(template.render())

    def post(self):

        taskqueue.add(
            url='/_test/execute',
            params={
                'line_bytes': self.request.get('line_bytes'),
                'line_count': self.request.get('line_count'),
                'flush_count': self.request.get('flush_count'),
                'entity_count': self.request.get('entity_count'),
            }
        )

        self.redirect('/_test/config')


class LogTestHandler(webapp2.RequestHandler):
    """Execute the test case."""
    def post(self):

        line_bytes = int(self.request.get('line_bytes'))
        line_count = int(self.request.get('line_count'))
        flush_every = int(self.request.get('flush_count'))
        entity_count = int(self.request.get('entity_count'))

        logging.info("Test Specs: %s", {
            'line_bytes': line_bytes,
            'line_count': line_count,
            'flush_every': flush_every,
            'entity_count': entity_count,
        })
        #logservice.flush()

        repeat_count = max(1, line_bytes / len(string.ascii_letters))
        logging_data = list(
            itertools.repeat(string.ascii_letters, repeat_count))

        for line in xrange(line_count):
            random.shuffle(logging_data)
            logging.info("%s: %s", line, ''.join(logging_data))

            if flush_every and not line % flush_every:
                logservice.flush()

        logging.info("Writing entities")
        db.put(Entity(keyname=i) for i in xrange(100))
        logging.info("Done writing entities")

config = {
    'webapp2_extras.jinja2': {
        'template_path': 'example/templates'
    }
}

app = webapp2.WSGIApplication([
    ('/_test/config', ConfigHandler),
    ('/_test/execute', LogTestHandler),
], config=config)


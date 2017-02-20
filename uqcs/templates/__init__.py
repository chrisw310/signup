from mako.lookup import TemplateLookup
import os

emails_dir = os.path.join(os.path.dirname(__file__), '..', 'emails')

lookup = TemplateLookup([os.path.dirname(__file__), emails_dir])
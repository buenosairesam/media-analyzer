# Import environment-specific settings
import os

from .base import *

env = os.environ.get("DJANGO_ENV", "development")

if env == "production":
    from .production import *
else:
    from .development import *

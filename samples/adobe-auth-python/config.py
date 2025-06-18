import os

class Config(object):
    FLASK_SECRET = os.environ.get('FLASK_SECRET', '497d2981e991ecb18eab2da404b9530b5e354db5ed694e6d310d85d07306972a')
    ADOBE_API_KEY = os.environ.get('ADOBE_API_KEY', 'd295d2240bcf4299be9917c05b8c6052')
    ADOBE_API_SECRET = os.environ.get('ADOBE_API_SECRET', 'p8e-KBZlfKyP1w2nNC8eRPU1-tJfzQ-2fXzD')
import io
import os
import sys
from shutil import rmtree
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = '\n' + f.read()

setup(name='ziproto',
        version='1.0',
        description='Protocol Buffer used to serialize and compress data',
        long_description=long_description,
        long_description_content_type='text/markdown',
        author='Zi Xing Narrakas',
        author_email='203818872@qq.com`',
        url='https://bitbucket.org/ziproto/python/',
        python_requires='>=3.6.0',
        include_package_data=True,
        py_modules=[
            'ziproto',
            'ziproto.ValueType',
            'ziproto.Headmap',
            'ziproto.ZiProtoFormat',
            'ziproto.ZiProtoEncoder',
            'ziproto.ZiProtoDecoder'
        ]
)

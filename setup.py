import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="AsyncAPY",
    version="0.1",
    author="Mattia Giambirtone",
    author_email="hackhab@gmail.com",
    description="A full-fledged library to build Asynchronous API Servers in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/intellivoid/Internal-API-Server",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)

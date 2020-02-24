import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="lituyamon", # Replace with your own username
    version="0.3.0",
    author="Matt Jones",
    author_email="gitcode@magisa.org",
    description="Lituya monitoring package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mbjones/lituyamon",
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
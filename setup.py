import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="lituyamon",
    version="0.8.2",
    author="Matt Jones",
    author_email="gitcode@magisa.org",
    description="Shipboard monitoring package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mbjones/lituyamon",
    packages=setuptools.find_packages(where="src"),
    entry_points ={
        'console_scripts': [
            'lituyamond = lituyamon:main'
        ]
    },
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)

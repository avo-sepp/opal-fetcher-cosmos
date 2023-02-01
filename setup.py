from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='opal-fetcher-cosmosdb',
    version='0.0.1',
    author='Avo Sepp',
    author_email="",
    description="An OPAL fetch provider to bring authorization state from CosmosDB.",
    long_description_content_type="text/markdown",
    long_description=long_description,
    url="https://github.com/avo-sepp/opal-fetcher-cosmosdb",
    packages=find_packages(),
    classifiers=[
        'Operating System :: OS Independent',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'
    ],
    python_requires='>=3.7',
    install_requires=[
        'opal-common>=0.1.11',
        'azure-identity',
        'azure-cosmos',
        'pydantic',
        'tenacity',
        'click'
    ],
)

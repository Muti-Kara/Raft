from setuptools import setup, find_packages

setup(
    name='raft-cluster',
    version='0.0.1',
    author='Muti-Kara',
    author_email='muti.kara@ug.bilkent.edu.tr',
    description='A Raft library.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Muti-Kara/Raft',
    packages=find_packages(),
    install_requires=[
        'pydantic',
        'fastapi',
        'uvicorn',
        'rpyc'
    ],
    entry_points={
        'console_scripts': [
            'run-cluster-manager=main:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.11',
    ],
)
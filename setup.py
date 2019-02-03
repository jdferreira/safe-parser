import setuptools

with open('README.md') as f:
    long_description = f.read()

setuptools.setup(
    name='safe-parser',
    version='0.1.1',
    author='João D. Ferreira',
    author_email='jotomicron@gmail.com',
    description='A simple parser of python-line code that can be safely executed',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/jdferreira/safe-parser',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)

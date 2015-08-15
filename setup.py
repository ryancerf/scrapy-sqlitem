from setuptools import setup, find_packages

try:
   import pypandoc
   description = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError):
    print("could not import README.md and convert.  Is pypandoc installed?")
    description = open('README.md').read()

setup(
    name='scrapy-sqlitem',
    version='0.1.2',
    url='https://github.com/ryancerf/scrapy-sqlitem',
    description='Scrapy extension to save items to a sql database',
    long_description=description,
    author='Ryan Cerf',
    author_email='ryancerf@yahoo.com',
    license='BSD',
    packages=find_packages(exclude=('tests', 'tests.*', 'example_project', 'example_project.*')),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Framework :: Scrapy',
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities',
        'Framework :: Scrapy',
    ],
    requires=['scrapy (>=0.24.5)', 'sqlalchemy'],
)

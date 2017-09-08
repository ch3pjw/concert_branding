from setuptools import setup, find_packages

setup(
    name='concert_branding',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    decsription='Brand assets for Concert',
    keywords=['svg', 'xml'],
    url='http://github.com/concert/branding',
    author='Paul Weaver',
    author_email='paul@concertdaw.co.uk',
    version='0.0.0',
    license='',
    install_requires=[],
    dependency_links=[
        'http://github.com/concert/svgast/tarball/master#egg=svgast-0.0'
    ]
)

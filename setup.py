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
    install_requires=[
        'svgast==0.0.0',
        'argh'
    ],
    dependency_links=[
        'https://github.com/concert/svgast/archive/master.zip#egg=svgast-0.0.0'
    ]
)

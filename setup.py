from setuptools import setup, find_packages
import sys, os

version = '0.8'

long_description = ''
if os.path.isfile('README.txt'):
    long_description=open('README.txt').read() + open('CHANGES.txt').read()

setup(name='freeboxtv',
      version=version,
      description="VLC launcher for Freebox TV",
      long_description=long_description,
      classifiers=[
          'Environment :: Console',
          'License :: OSI Approved',
          'Operating System :: POSIX',
          'Topic :: Home Automation',
      ],
      keywords='freebox',
      author='Gael Pasgrimaud',
      author_email='gael@gawel.org',
      url='http://www.gawel.org/docs/dist',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      fbxtv = freeboxtv:main
      """,
      )

from distutils.core import setup

from setuptools import find_packages


setup(
    name='timer_event',
    packages=find_packages('src'),
    version="0.7.3",
    author="Erol Yesin",
    author_email='erol@sandboxzilla.com',
    description='The package offers thread-safe classes for event-driven programming, including a versatile Event class for managing callback routines and a TimerEvent class for creating repeated timer-based events.',
    download_url='https://github.com/erolyesin/timer_event/archive/refs/tags/v0.07.02-beta.tar.gz',
    keywords=["event", "thread-safe", "event-driven",
              "timer-based events", "repeated events", "callback"],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)

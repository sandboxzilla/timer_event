from distutils.core import setup


setup(
    name='TimerEvent',
    packages=find_packages('src'),
    version='0.7',
    license='MIT',
    author="Erol Yesin",
    author_email='erol@sandboxzilla.com',
    description='The Timer Event package provides classes for creating timed threaded events',
    download_url='https://github.com/user/erolyesin/release/v_07.tar.gz',
    keywords=['Event', 'Thread', 'Timer'],
    install_requires=[],
    classifiers=[
        'Development Status :: 3 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License', 
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)

from setuptools import setup, find_packages


setup(
    name='TimerEvent',
    version='0.7',
    license='MIT',
    author="Erol Yesin",
    author_email='erol@sandboxzilla.com',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://github.com/erolyesin/timer_event',
    keywords='python timer event',
    install_requires=[],
)

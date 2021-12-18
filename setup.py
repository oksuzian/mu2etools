import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='mu2etools',
    version='0.0.1',
    author='Yuri Oksuzian',
    author_email='oksuzian@gmail.com',
    description='Packages for cosmic analysis',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/oksuzian/mu2etools',
    project_urls = {
        "Bug Tracker": https://github.com/oksuzian/mu2etools/issues"
    },
    license='MIT',
    packages=['mu2etools'],
    install_requires=['requests'],
)

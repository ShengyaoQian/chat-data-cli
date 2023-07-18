from setuptools import setup, find_packages

setup(
    name='chat-data-cli',
    version='0.1',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'chat-data=chat_data.chat:main',
        ],
    },
    install_requires=[
        'openai',
        'mysql-connector-python',
        'termcolor',
        'inquirer',
    ],
    author='Shengyao Qian',
    author_email='qianshengyao13@gmail.com',
    description='A command line tool to chat data with GPT.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/ShengyaoQian/chat-data-cli',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)

from setuptools import setup

setup(
    name='mailer',
    version='1.0',
    py_modules=['mailer'],
    install_requires=[
        'pyTelegramBotAPI',
        'colorama',
        'pyautogui',
        'requests'
    ],
)
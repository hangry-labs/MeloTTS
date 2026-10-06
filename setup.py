import os 
from setuptools import setup, find_packages


cwd = os.path.dirname(os.path.abspath(__file__))
version_file = os.path.join(cwd, 'VERSION')

with open(version_file, encoding='utf-8') as f:
    display_version = f.read().strip()

package_version = display_version.removeprefix('v').replace('-SNAPSHOT', '.dev0')

with open('requirements.txt') as f:
    reqs = [
        requirement.replace('+cu130', '')
        for requirement in f.read().splitlines()
        if requirement and not requirement.startswith('--')
    ]

setup(
    name='melotts',
    version=package_version,
    python_requires='>=3.13,<3.14',
    packages=find_packages(),
    include_package_data=True,
    install_requires=reqs,
    package_data={
        '': ['*.txt', 'cmudict_*'],
        'melo.standalone_ui': [
            'static/*.html',
            'static/*.css',
            'static/*.js',
            'static/locales/*.json',
            'static/vendor/lucide/*',
            'static/vendor/wavesurfer/*',
            'static/vendor/wavesurfer/plugins/*',
        ],
    },
    entry_points={
        "console_scripts": [
            "melotts = melo.main:main",
            "melo = melo.main:main",
            "melo-ui = melo.app:main",
        ],
    },
)

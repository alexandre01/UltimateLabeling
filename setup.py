from setuptools import setup

# extract version from __init__.py
with open('ultimatelabeling/__init__.py', 'r') as f:
    VERSION_LINE = [l for l in f if l.startswith('__version__')][0]
    VERSION = VERSION_LINE.split('=')[1].strip()[1:-1]

setup(
    name='ultimatelabeling',
    version=VERSION,
    packages=[
        'ultimatelabeling',
        'ultimatelabeling.views',
        'ultimatelabeling.models',
        'ultimatelabeling.styles',
        'ultimatelabeling.siamMask',
        'ultimatelabeling.siamMask.models',
        'ultimatelabeling.siamMask.utils'
    ],
    license='MIT',
    description='A multi-purpose Video Labeling GUI in Python with integrated SOTA detector and tracker.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Alexandre Carlier',
    author_email='alexandre.carlier01@gmail.com',
    url='https://github.com/alexandre01/UltimateLabeling',


    install_requires=[
       'PyQt5',
        'opencv-contrib-python',
        'paramiko',
        'scp',
        'pynput',
        'numpy',
        'tqdm',
        'torch',
        'pillow',
        'matplotlib',
        'pandas',
        'scipy'
    ],
    extras_require={
            'test': [
                'pytest',
            ],
    },

    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
    ],
)

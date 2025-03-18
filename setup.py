from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="devassist",
    version="0.1.0",
    author="DevAssist Team",
    author_email="example@example.com",
    description="An autonomous development assistant for software development tasks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/username/devassist",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.11",
    install_requires=[
        "pyyaml>=6.0",
        "openai>=1.0.0",
        "anthropic>=0.5.0", 
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "rich>=13.0.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "playwright>=1.40.0",
    ],
    entry_points={
        "console_scripts": [
            "devassist=devassist.main:main",
        ],
    },
)
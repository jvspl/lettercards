from setuptools import setup


setup(
    name="lettercards",
    version="0.1.0",
    description="CLI for generating toddler letter learning cards",
    py_modules=["generate", "process_photo", "pictogram_workflow", "deck_state"],
    packages=["lettercards"],
    install_requires=[
        "pillow>=9.0.0",
        "reportlab>=4.0.0",
    ],
    entry_points={
        "console_scripts": [
            "lettercards=lettercards.cli:main",
        ],
    },
)

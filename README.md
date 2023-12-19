# get-post-data
First ever desktop application written in PyQt5 to scrape medium and twitter posts.

## Installation
**Requirement**: poetry installed.
Installing related packages:
```
poetry install
```

Installing pyqtwebengine with following commands:
```
poetry run python -m pip wheel --use-pep517 "pyqtwebengine (==5.15.6)"
poetry add pyqtwebengine@5.15.6
```

Note: Removing pyqtwebengine wheel packages is optional.

## Getting started
To start the application in development mode: 
```
poetry run dev
```

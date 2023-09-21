# CS316 Project

This is our repo for the sports arbitrage project.

After cloning or downloading the project, make sure your working directory is sports-arbitrage (or whatever you called it).

To run locally, create a virtual environment, e.g.

```python -m venv my_venv```

Then activate the virtual environment with

```source my_venv/bin/activate```

Then install the necessary packages with

```pip install -r requirements.txt```

If you do not have postgres installed, you will need to do that as well, which you could do here: [https://www.postgresql.org/download/](https://www.postgresql.org/download/)

You will now need to set up the database that the project uses.

If postgres is installed correctly, the following steps should work.

1. Enter ```psql postgres``` in the terminal.
2. Run ```create database arbitrage_db;```.

### TODO: Add specifics on what .env configuration should be

Now, to run the project, enter ```python main.py``` and go to http://127.0.0.1:5000 in your browser.





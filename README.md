# CS316 Project

This is our repo for the sports arbitrage project.

After cloning or downloading the project, make sure your working directory is sports-arbitrage (or whatever you called it).

To run locally, create a virtual environment, e.g.

```python -m venv my_venv```

Then activate the virtual environment with

```source my_venv/bin/activate```

Then install the necessary packages with

```pip install -r requirements.txt```

If you do not have postgres installed. Redis is also needed for asynchronous and automated data insertion. If this is not possible, data updates can be done with the "fetch new data" on the games page.

You will now need to set up the database that the project uses.
If postgres is installed correctly and is running, the following steps should work.

1. Enter ```psql postgres``` in the terminal.
2. Run ```create database arbitrage_db;```.

Now we must configure the environment variables. Create a .env file in the project directory.

Add the following:
```SECRET_KEY="<put whatever you want here>"``
```DB_USERNAME="<your username>"```
```DB_PASSWORD="<your password>"```
```DATABASE_URL="postgres://<your username>:<your password>!@localhost:5432/arbitrage_db"```
```FLASK_APP="main"```
```API_KEY="<API_KEY>"```

For the API_KEY, you will need to go to TheOddsApi and get your own key.

Now, to run the project, enter ```python main.py``` and go to http://127.0.0.1:5000 in your browser.

If Redis is not already running, enter ```brew services start redis``` in the terminal. 

To start Celery beat, open a new terminal window and run ```celery -A make_celery beat --loglevel=info```

To start the Celery workers, open a new terminal window and run ```celery -A make_celery worker --loglevel=info```.






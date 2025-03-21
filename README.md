SmallBlog
======
![](app/static/screenshot-index-page.jpg)
[View the live project here](https://aldosebastian.com/smallblog/)

# Table of Contents
1. [Introduction](#introduction)
2. [Database](#database)
3. [Features](#features)
4. [Testing](#testing)
5. [Deployment](#deployment)

## Introduction
This is one of my hobby projects, to learn a new framework that is different to what I usually use at work. It is a blogging platform, where users can register, post their thoughts, and interact with each other by following each other, commenting and voting on others' posts.

Main programming languages used:

  * Python
  * JavaScript
  * CSS3
  * HTML5
  * SQL

Libraries and Frameworks used:
  * Flask (for back-end)
  * Bootstrap 5 (to easily style the whole blog)
  * SQLAlchemy (ORM to conduct CRUD operations with the database)
  * jQuery (To help ease client-side data processing)
  * Alembic (Database migration tool, to help update the database with schema changes (e.g. addition or deletion of a column for a particular table))
  * Jinja2 (Templating language for Flask to help display backend data to frontend)
  * Unittest (To test the application automatically)

CI/CD and deployment:
  * DigitalOcean as the Linux server where the live blog is currently deployed
  * Docker (To ease deployment of the app)
  * GitHub Action (To automate testing and deployment of the blog to the live server)
  * Git (Version control)
  * Gunicorn (A Python WSGI HTTP server used to serve the application in the live server)

## Database

The database schema is as shown below, generated using [drawsql.app](drawsql.app). SQLite is used as the development and testing database,
and MYSQL is used in the live blog (i.e. production).

![data](app/static/database.JPG)

Some notes on the database schema:

* To ensure unique users, the ```users``` table requires unique ```email``` and ```username``` column values.
* Only password hashes are being stored in the database. Any password input for login are hashed using a particular hash algorithm and the generated value compared against the one stored.

* ```roles``` table allow us to group users into different types; currently they are generic users, moderators and administrators, each with different permissions. These are assigned to each user and processed in ```models.py```.
* ```posts``` and ```comments``` tables have ```title_html``` and ```body_html``` columns. These are filtered inputs of posts and comments to the blog, and the raw input is stored in ```title``` and ```body``` columns respectively. 

  The ```_html``` versions are the ones used in rendering the posts and comments to the blog. The filter is needed to avoid any risks of being attacked with ```HTML``` or ```JavaScript``` injection, for example inputs such as ```<script>alert('xss')</script>```, which if used could render dangerous outputs to the blog, such as login forms or buttons that lead to malicious websites. The ```Jinja2``` renderer used, actually already implement their own filters to any values to be rendered. However, since the posts and comments allow markdown input, I have my own filters for extra security.
* The ```follows``` and ```votes``` tables are association tables. ```follows``` table cover the many-to-many relationship between ```users``` and ```users``` table. ```votes``` table cover the one-to-many relationship between ```users``` and ```votes```, and many-to-one between ```votes``` and ```posts```. These represent the fact that one user can follow and be followed by multiple users, and that a user can vote for multiple posts and that a post can have multiple votes.

  The ```follower_id``` and ```following_id``` are foreign keys of the ```follows``` association table, and ```voter_id``` and ```post_id``` are foreign keys for the ```votes``` association table.

* Validation of input (e.g. email has to be of format a@email.com) is done at the server-side, using Python packages such as ```flask-form```.
* No index column is made on any of the tables, I'll add this in the future to speed up queries.

## Deployment
### Local machine
To deploy the project in your own system:
* Download ```Python 3.9.5``` or higher to your system, and ```sqlite3``` for the database
* Fork this repository, open up a terminal session, and navigate to the forked repository
* Create a virtual environment (recommended) using ```python -m venv venvYourName```
* Install all Python requirements using ```python -m pip install -r requirements/common.txt```
* Create an environment variable in the terminal ```FLASK_APP``` with value ```blogging.py```, and
```SECRET_KEY``` with a hard to guess string as its value; you can create one here [https://randomkeygen.com/](https://randomkeygen.com/)
* Run the command ```flask run``` in the terminal, and navigate to ```localhost:5000``` in your browser. A database ```data-dev.sqlite``` will automatically be created and used by your system.

### Docker
Alternatively, you can use Docker to deploy:
 * Download and install [docker](https://docs.docker.com/compose/install/compose-desktop/) in your system
 * Create a new folder in your file system, and copy the file ```docker-compose.yml``` and ```Dockerfile``` from this repository to that folder, and then do `docker-compose build .`. Alternatively instead of local build, download the docker image for this blog by running ```docker pull aldosebastian/blogging``` (login to your Dockerhub account first).
 * Finally, run ```docker-compose up -d``` to start the blog server in the background, open up your browser and go to ```localhost:8000```
 * To stop the blog from running, type ```docker-compose down```
 
 ## Testing
The folder ```tests``` contains unit tests for the application. To run all the tests, simply run ```flask test```

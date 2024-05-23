https://libsys-api-b88eb4c3d18e.herokuapp.com/

# flask_library
Lite library system as website in Flask.

A website that helps you manage your library. By taking care of storing data about books, clients and borrows.
Clients can also register and get informations about availability of books and check out their accounts.

(python 3.10)

(create a virtual environment with python 3.10 and activate it before installing the requirements)
(you can change TESTING = True in config.py)

## Installation
1. Clone the repository
2. Install the requirements
   ```bash
    pip install -r requirements.txt
    ```
3. Set proper environment variables (.env file on linux)
   ```bash
    SECRET_KEY=test
    MAIL_SERVER=...
    MAIL_PORT=...
    MAIL_USE_TLS=...    #(0 or 1)
    MAIL_USE_SSL=...    #(0 or 1)
    MAIL_USERNAME=...
    MAIL_PASSWORD=...
    MAIL_DEFAULT_SENDER=...
    ```
4. Run unit tests
   ```bash
    python3 -m flask test
    ```
5. Initialize the database and fill it with data
   ```bash
    python3 -m flask init-db
    python3 -m flask insert-test-data
    ```
6. Run the application
   ```bash
    python3 -m flask run
    ```

-*-

ADMIN (mail | password): test@test.admin | test

MODERATOR (mail | password): test@test.moderator | test

USER (mail | password): test@test.user | test

INACTIVE USER (mail | password): test@test.user-inactive | test


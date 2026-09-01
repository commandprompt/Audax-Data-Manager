# Run your local development copy of PgManage on Ubuntu

## Install the necessary OS packages
```
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install git libssl-dev python-protobuf build-essential
sudo apt-get install python3.9 python3.9-dev python3.9-venv python3-wheel libpq-dev libldap2-dev libsasl2-dev
```

## Set up app environment
Clone pgmanage repository; change to the root directory of cloned repository, checkout dev branch:
```
git clone https://github.com/commandprompt/audax-data-manager.git
cd pgmanage
git checkout dev
```
## Install Dependencies and Run the App

1. Activate the Python virtual environment created in the previous step:
```shell
python3.9 -mvenv .env
source .env/bin/activate
```

2. Install Python dependencies using pip:
```shell
pip install -r requirements.txt
```

3. Navigate to the pgmanage/app/static/assets/js/pgmanage_frontend/ directory and install front-end Node.js dependencies using npm:
> [!NOTE]
> Node.js version 18.x is required
```shell
cd pgmanage/app/static/assets/js/pgmanage_frontend/
npm install
```

4. Start a development front-end server:
```shell
npm run dev
```

5. In a separate terminal session navigate to the pgmanage subdirectory of the project and start the application back-end service by running:
```shell
cd [project_root]/
source .env/bin/activate
cd pgmanage
./manage.py runserver
```

6. When you see that the application server is ready, open http://localhost:8000 in your preferred web browser.

7. Log in using the following credentials:
    - Username: admin
    - Password: admin

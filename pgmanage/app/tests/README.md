# Backend tests

Most tests use Django's local test database. The PostgreSQL and SQL Server
integration tests additionally require the sample databases defined in
`docker-compose.yml`.

## Prerequisites

- Python 3.11 with the project dependencies installed (`poetry install`)
- Docker with the Compose plugin
- `curl` and `unzip` for downloading the external fixtures

Run the fixture and Docker Compose commands below from this directory.

## Download test data

The database fixtures are intentionally not committed because of their size.

```bash
./fetch-test-data.sh
```

To download only one fixture:

```bash
./fetch-test-data.sh northwind
./fetch-test-data.sh dellstore
```

## Start the test databases

Start all test database services together:

```bash
docker compose up
```

Alternatively, start the services individually as described below.

Start PostgreSQL in the background:

```bash
docker compose up -d postgres_test_db
```

Start SQL Server and run the Northwind initializer in the foreground:

```bash
docker compose up mssql_test_db_init
```

## Run tests

From the repository root, run the complete backend test suite with:

```bash
poetry run python pgmanage/manage.py test app.tests
```


## Cleanup

Stop and remove the test containers and network:

```bash
docker compose down
```

The Compose configuration does not use named database volumes, so removing the
containers also removes their database state. Downloaded SQL fixture files
remain in this directory and can be reused.

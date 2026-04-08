# Dev environment security recommendations

## Dependency update rules
pin all project 3rd party dependencies to a specific version
when updating dependency use the following critera to select new dependency version:
    - it should not introduce breaking changes to the project codebase unless the intention of upgrade is to address critical issues with the curent dependency version
    - it should contain valuable fixes or new features necessary for the project
    - it should be released at least one month ago, so we can minimize the chance of being "patient zero" in a potential supply chain attack
do not update all dependencies blindly, go over each one and verify that the new version meets the update criteria
always run npm audit after bumping dependencies, commit library bump changes only if audit passes
use pip-audit to check python stack for potential security issues
always commit depenency .lock files when update is complete
use dependency hashes when exporting requirements.txt to prevent potential changes to pre-existing packgages

## Containerized dev environment
Running your development servers and package management commands in Docker containers may help to prevent any malicious code from accessing your private data like ssh keys, tokens etc. 
### Starting dev env
cd $project_root
`docker compose up`
This command spins-up two development containers (front-end and back-end). These containers mount project source files and vite/django processes will auto-reload on code changes as usual

### Running dependency audit (npm audit and pip-audit) and other service commands
cd $project_root
`docker compose run --rm backend-audit`
will start a separate service container to run pip-audit against currently installed project depdendencies

`docker compose run --rm frontend-audit`
will start a separate service container to run npm audit against currently installed project front-end depdendencies

`docker compose run --rm frontend-npminstall` installs front-end depedencies (internally it just runs npm install in pgmanage_frontend)
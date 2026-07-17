#this script is intended to be run under cygwin + win10 environment
#make sure you have installed NSIS and Resource Hacker software
#run as ./deploy.sh 1.0b, replace the actual version number with the correct one
set -e

APP_VERSION="$1"
REPO="https://github.com/commandprompt/pgmanage"

BRANCH="${2:-master}"
DEPLOY_DIR=$(pwd)
# TEMP_DIR=$DEPLOY_DIR/tmp
# use this when building in virtualbox
TEMP_DIR=/cygdrive/c/pgmanage_tmp

# if version is not provided, we use last tag from repository
if [ -z "$APP_VERSION" ]
then
    # Fetch all tags from remote repository
    git fetch --all --tags

    # Get last tag version
    APP_VERSION=$(git describe --tags $(git rev-list --tags --max-count=1))
fi

NWJS_URL='https://dl.nwjs.io/v0.77.0/nwjs-v0.77.0-win-x64.zip'
NWJS_ARCHIVE='nwjs-v0.77.0-win-x64.zip'
NWJS_DIR='nwjs-v0.77.0-win-x64'

APP_LONG_VERSION=PgManage.$APP_VERSION

echo "making release dir: release_$APP_VERSION"
rm -rf release_$APP_VERSION $TEMP_DIR
mkdir release_$APP_VERSION $TEMP_DIR

cd $TEMP_DIR

echo "Cloning repository $REPO"
git clone $REPO --depth 1 -b $BRANCH .

echo "creating virtual env"
python -m venv venv

dos2unix venv/Scripts/activate
source venv/Scripts/activate

# Install all required libraries
echo "installing python dependencies"
pip3 install -r requirements.txt
pip3 install pyinstaller==5.13.2
# use pipdeptree to troubleshoot dependency issues
# pipdeptree
cd pgmanage/

# set up versions in custom_settins.py
echo "setting app version in sources to $APP_VERSION"
sed -i "s/Dev/PgManage $APP_VERSION/" pgmanage/custom_settings.py
sed -i "s/dev/$APP_VERSION/" pgmanage/custom_settings.py

# building vite bundle
cd app/static/pgmanage_frontend/

echo "installing javascript dependencies"
npm install

echo "building vite bundle"
npm run build

cd $TEMP_DIR/pgmanage

echo "running pyinstaller"
touch pgmanage.db
pyinstaller ./audaxdm-win.spec
pyinstaller ./process_executor-win.spec
mv dist/audaxdm-server $DEPLOY_DIR/release_$APP_VERSION/
mv dist/process_executor $DEPLOY_DIR/release_$APP_VERSION/audaxdm-server/

cd $DEPLOY_DIR
curl -C - -LO $NWJS_URL
unzip -o $NWJS_ARCHIVE -d $TEMP_DIR/

mv $TEMP_DIR/$NWJS_DIR/* release_$APP_VERSION/
mv release_$APP_VERSION/nw.exe release_$APP_VERSION/audaxdm-app.exe
cp $TEMP_DIR/deploy/app/index.html release_$APP_VERSION
cp $TEMP_DIR/deploy/app/package.json release_$APP_VERSION
cp $TEMP_DIR/deploy/app/audaxdm_icon.png release_$APP_VERSION

sed -i "s/version_placeholder/v$APP_VERSION/" release_$APP_VERSION/index.html
# install resource hacker with default path, then uncomment these lines to replace the default pyinstaller and nwjs exe icons

/cygdrive/c/Program\ Files\ \(x86\)/Resource\ Hacker/ResourceHacker.exe -open release_$APP_VERSION/audaxdm-app.exe -save release_$APP_VERSION/pgmanage-app.exe -action addoverwrite -res ./win-icon.ico -mask ICONGROUP,IDR_MAINFRAME,
/cygdrive/c/Program\ Files\ \(x86\)/Resource\ Hacker/ResourceHacker.exe -open release_$APP_VERSION/audaxdm-server/audaxdm-server.exe -save release_$APP_VERSION/audaxdm-server/audaxdm-server.exe -action addoverwrite -res ./win-icon.ico -mask ICONGROUP,IDR_MAINFRAME,


/cygdrive/c/Program\ Files\ \(x86\)/NSIS/makensisw.exe /DSRCDIR=release_$APP_VERSION /DVERSION=$APP_VERSION install_script.nsi

echo "deactivating virtual env and cleaning temp folder"

# deactivate virtualenv
deactivate

# clean temp folder
rm -rf $TEMP_DIR

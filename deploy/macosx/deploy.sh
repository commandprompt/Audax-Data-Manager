#!/bin/bash

# Build script to create Mac App Bundle for pgmanage

# Exit when any command fails
set -e -e

APP_VERSION="$1"
REPO="https://github.com/commandprompt/pgmanage"
BRANCH="${2:-master}"
DEPLOY_DIR=$(pwd)
TEMP_DIR=$DEPLOY_DIR/tmp

# if version is not provided, we use last tag from repository
if [ -z "$APP_VERSION" ]
then
    # Fetch all tags from remote repository
    git fetch --all --tags

    # Get last tag version
    APP_VERSION=$(git describe --tags $(git rev-list --tags --max-count=1))
fi

NWJS_URL='https://dl.nwjs.io/v0.77.0/nwjs-v0.77.0-osx-x64.zip'
NWJS_ARCHIVE='nwjs-v0.77.0-osx-x64.zip'
NWJS_DIR='nwjs-v0.77.0-osx-x64'

APP_LONG_VERSION=pgmanage-$APP_VERSION
APP_NAME=PgManage
RELEASE_DIR=$DEPLOY_DIR/release_$APP_VERSION

rm -rf $RELEASE_DIR $TEMP_DIR
mkdir $RELEASE_DIR $TEMP_DIR

cd $TEMP_DIR

echo "cloning repository $REPO"
git clone $REPO --depth 1 -b $BRANCH .

# Install pyenv to manage specific python version
brew update && brew upgrade
brew install pyenv
brew install xz

# Install Python 3.11.15 and create virtual environment
env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.11.15 --skip-existing

pyenv local 3.11.15
PYTHON_EXE=$(pyenv which python)
$PYTHON_EXE -m venv venv
source venv/bin/activate

# Install all required libraries
echo "installing python dependencies"
pip3 install -r requirements.txt
pip3 install pyinstaller==5.13.2

cd pgmanage/

echo -n "Switching to Release Mode..."
sed -i -e 's/DEV_MODE = True/DEV_MODE = False/g' pgmanage/custom_settings.py
echo "Done."

echo -n "Switching to Desktop Mode... "
sed -i -e 's/DESKTOP_MODE = False/DESKTOP_MODE = True/g' pgmanage/custom_settings.py
echo "Done."

# building vite bundle
cd app/static/pgmanage_frontend/

echo "installing javascript dependencies"
npm install

echo "building vite bundle"
npm run build

cd $TEMP_DIR/pgmanage

# Do a small clean-up
echo -n "Removing sass and map files"
find ./ -name "*.map" -delete
find ./ -name "*.scss" -delete

touch pgmanage.db

# set up versions in custom_settins.py
sed -i '' "s/Dev/Audax Data Manager $APP_VERSION/" pgmanage/custom_settings.py
sed -i '' "s/dev/$APP_VERSION/" pgmanage/custom_settings.py

echo "running pyinstaller"
pyinstaller pgmanage-mac.spec
pyinstaller process_executor-mac.spec

mkdir pgmanage-server 
echo 'Removing signature from libpython3.11.dylib library'
codesign --remove-signature dist/pgmanage-server/libpython3.11.dylib
mv dist/process_executor pgmanage-server/
mv dist/pgmanage-server/* pgmanage-server/

cd $DEPLOY_DIR

curl -C - -LO $NWJS_URL
unzip $NWJS_ARCHIVE -d $TEMP_DIR

cd $TEMP_DIR
mv $NWJS_DIR/nwjs.app $APP_LONG_VERSION.app

mkdir $APP_LONG_VERSION.app/Contents/Resources/app.nw
mv pgmanage/pgmanage-server $APP_LONG_VERSION.app/Contents/Resources/app.nw/

cp deploy/app/* $APP_LONG_VERSION.app/Contents/Resources/app.nw/
sed -i '' "s/version_placeholder/v$APP_VERSION/" $APP_LONG_VERSION.app/Contents/Resources/app.nw/index.html

# Replace default icons with pgmanage icon
cp $DEPLOY_DIR/mac-icon.icns $APP_LONG_VERSION.app/Contents/Resources/app.icns
cp $DEPLOY_DIR/mac-icon.icns $APP_LONG_VERSION.app/Contents/Resources/document.icns

# removes unnecessary keys from Info.plist
plutil -remove ASWebAuthenticationSessionWebBrowserSupportCapabilities $APP_LONG_VERSION.app/Contents/Info.plist
plutil -remove CFBundleDocumentTypes $APP_LONG_VERSION.app/Contents/Info.plist
plutil -remove CFBundleURLTypes $APP_LONG_VERSION.app/Contents/Info.plist
plutil -remove UTExportedTypeDeclarations $APP_LONG_VERSION.app/Contents/Info.plist
plutil -remove UTImportedTypeDeclarations $APP_LONG_VERSION.app/Contents/Info.plist

# Set up correct application name
plutil -replace CFBundleName -string "$APP_NAME" $APP_LONG_VERSION.app/Contents/Info.plist

plutil -replace CFBundleDisplayName -string "$APP_NAME" $APP_LONG_VERSION.app/Contents/Info.plist

plutil -replace CFBundleExecutable -string "$APP_NAME" $APP_LONG_VERSION.app/Contents/Info.plist

plutil -replace CFBundleShortVersionString -string $APP_VERSION $APP_LONG_VERSION.app/Contents/Info.plist

echo CFBundleDisplayName = \"$APP_NAME\" >> $APP_LONG_VERSION.app/Contents/Resources/el.lproj/InfoPlist.strings

# rename nwjs executable
mv $APP_LONG_VERSION.app/Contents/MacOS/nwjs $APP_LONG_VERSION.app/Contents/MacOS/$APP_NAME

mv $APP_LONG_VERSION.app $RELEASE_DIR/$APP_NAME.app

# Create dmg file

# Install dmgbuild command line tool
pip3 install dmgbuild

dmgbuild -s $DEPLOY_DIR/settings.py -D app=$RELEASE_DIR/$APP_NAME.app "$APP_NAME" "$APP_LONG_VERSION"_mac_x64.dmg

mv "$APP_LONG_VERSION"_mac_x64.dmg $RELEASE_DIR

# Remove tmp folder
cd $DEPLOY_DIR

echo "deactivating virtual env and cleaning temp folder"

deactivate

rm -rf $TEMP_DIR

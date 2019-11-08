echo "Setting up UNIS-RT..."


sudo python3.6 -m pip install jsonschema

cd lace
sudo python3.6 setup.py develop
cd -

cd unisrt
sudo python3.6 setup.py develop
cd -

echo "Building Controller"

sudo python3.6 -m pip install zof
sudo python3.6 -m pip install aiohttp

cd zof-topology
sudo python3.6 setup.py build install
cd -

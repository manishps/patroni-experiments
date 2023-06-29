source ../venv/bin/activate &&
rm -rf logs &&
mkdir logs &&
./make-conf.sh &&
patroni conf.yml

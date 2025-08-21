## install

### For AWS linux
```
sudo dnf update -y
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y openssl-devel bzip2-devel libffi-devel zlib-devel wget make
cd /usr/src
sudo wget https://www.python.org/ftp/python/3.12.2/Python-3.12.2.tgz 
sudo tar xzf Python-3.12.2.tgz
cd Python-3.12.2
sudo ./configure --enable-optimizations --prefix=/usr/local --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib"
sudo make altinstall
```

#### checking version
```
python3.12 --version
pip3.12 --version
sudo ln -s /usr/local/bin/python3.12 /usr/bin/python
```

### venv
```
cd [github-clonned-repo ]
python -m venv .venv
.venv/bin/pip3 --version
.venv/bin/python3 --versi1
.venv/bin/pip3 install -r requirements.txt
```
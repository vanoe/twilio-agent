## install

### For AWS linux
```
sudo pip3 install supervisor
sudo supervisorctl status
sudo echo_supervisord_conf > /etc/supervisord.conf
```

#### add these two lines at the end of /etc/supervisord.conf
```
[include]
files = /etc/supervisor/conf.d/*.conf
```

#### the file content you can get from config/server/supervisor.conf
```
sudo nano /etc/supervisor/conf.d/[SITE_NAME].conf
```

#### useful

```
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
sudo supervisorctl status
```

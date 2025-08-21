```
sudo dnf install nginx -y
sudo systemctl enable --now nginx
sudo dnf install certbot python3-certbot-nginx -y
sudo nano /etc/nginx/conf.d/twosol.conf
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl reload nginx
sudo certbot --nginx -d [SITE_NAME]
sudo certbot renew --dry-run
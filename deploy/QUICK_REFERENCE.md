# Quick Reference - AI Data Portal

## Perintah Penting

### Service Management
```bash
# Start aplikasi
sudo systemctl start ai-data-portal

# Stop aplikasi
sudo systemctl stop ai-data-portal

# Restart aplikasi
sudo systemctl restart ai-data-portal

# Cek status
sudo systemctl status ai-data-portal

# Lihat log (real-time)
sudo journalctl -u ai-data-portal -f

# Lihat 100 baris log terakhir
sudo journalctl -u ai-data-portal -n 100
```

### Nginx
```bash
# Test konfigurasi
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Restart nginx
sudo systemctl restart nginx

# Lihat error log
sudo tail -f /var/log/nginx/error.log
```

### Update Aplikasi
```bash
cd /var/www/ai_data_portal
source venv/bin/activate
git pull origin main                  # Jika pakai git
pip install -r requirements.txt       # Jika ada dependency baru
sudo systemctl restart ai-data-portal
```

### SSL Certificate
```bash
# Install SSL
sudo certbot --nginx -d your-domain.com

# Renew manual
sudo certbot renew

# Cek expiry date
sudo certbot certificates
```

### Troubleshooting
```bash
# Cek port yang dipakai
sudo lsof -i :8501
sudo lsof -i :80
sudo lsof -i :443

# Cek memory
free -h

# Cek disk
df -h

# Cek CPU
htop
```

## File Locations

| File | Lokasi |
|------|--------|
| Aplikasi | `/var/www/ai_data_portal/` |
| Virtual env | `/var/www/ai_data_portal/venv/` |
| Environment | `/var/www/ai_data_portal/.env` |
| Systemd service | `/etc/systemd/system/ai-data-portal.service` |
| Nginx config | `/etc/nginx/sites-available/ai-data-portal` |
| Nginx error log | `/var/log/nginx/error.log` |
| SSL certificates | `/etc/letsencrypt/live/your-domain.com/` |

## Checklist Deploy

- [ ] VPS sudah running Ubuntu 20.04/22.04
- [ ] SSH access ke VPS
- [ ] Domain sudah pointing ke IP VPS
- [ ] Upload file aplikasi ke `/var/www/ai_data_portal/`
- [ ] Jalankan `sudo bash install.sh`
- [ ] Edit `.env` dengan API key
- [ ] Setup SSL dengan certbot
- [ ] Test akses via browser

## Kontak

Jika ada masalah:
- Cek log terlebih dahulu
- Restart service
- Hubungi senior admin

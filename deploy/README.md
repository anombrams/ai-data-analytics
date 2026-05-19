# Panduan Deploy AI Data Portal ke VPS

## Persyaratan VPS

| Komponen | Minimum | Rekomendasi |
|----------|---------|-------------|
| OS | Ubuntu 20.04 | Ubuntu 22.04 |
| CPU | 1 core | 2 core |
| RAM | 2 GB | 4 GB |
| Storage | 10 GB | 20 GB |
| Bandwidth | 1 TB/bulan | Unlimited |

## Provider VPS yang Direkomendasikan
- DigitalOcean ($6/bulan)
- Vultr ($6/bulan)
- Linode ($5/bulan)
- AWS Lightsail ($5/bulan)
- IDCloudHost (lokal Indonesia)

---

## Langkah 1: Persiapan VPS

### 1.1 Login ke VPS via SSH
```bash
ssh root@IP_VPS_ANDA
```

### 1.2 Update sistem
```bash
apt update && apt upgrade -y
```

### 1.3 Buat user baru (jangan pakai root untuk production)
```bash
adduser aiportal
usermod -aG sudo aiportal
su - aiportal
```

---

## Langkah 2: Install Dependencies

### 2.1 Install Python & tools
```bash
sudo apt install -y python3.10 python3.10-venv python3-pip git nginx certbot python3-certbot-nginx
```

### 2.2 Verifikasi instalasi
```bash
python3 --version   # Harus 3.10+
nginx -v            # Harus terinstall
```

---

## Langkah 3: Upload & Setup Aplikasi

### 3.1 Buat direktori aplikasi
```bash
sudo mkdir -p /var/www/ai_data_portal
sudo chown -R aiportal:aiportal /var/www/ai_data_portal
```

### 3.2 Upload file aplikasi
**Opsi A: Via SCP (dari komputer lokal)**
```bash
# Jalankan di komputer lokal, bukan di VPS
scp -r /path/to/ai_data_portal/* aiportal@IP_VPS:/var/www/ai_data_portal/
```

**Opsi B: Via Git (jika sudah di repository)**
```bash
cd /var/www/ai_data_portal
git clone https://github.com/username/ai_data_portal.git .
```

**Opsi C: Via SFTP**
- Gunakan FileZilla atau WinSCP
- Connect ke VPS
- Upload semua file ke `/var/www/ai_data_portal/`

### 3.3 Setup Python virtual environment
```bash
cd /var/www/ai_data_portal
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.4 Test aplikasi berjalan
```bash
streamlit run app.py --server.port 8501
# Ctrl+C untuk stop setelah test berhasil
```

---

## Langkah 4: Setup Systemd Service

### 4.1 Copy file service
```bash
sudo cp /var/www/ai_data_portal/deploy/ai-data-portal.service /etc/systemd/system/
```

### 4.2 Reload dan start service
```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-data-portal
sudo systemctl start ai-data-portal
```

### 4.3 Cek status service
```bash
sudo systemctl status ai-data-portal
```

Jika berhasil, akan muncul `active (running)`.

---

## Langkah 5: Setup Nginx (Reverse Proxy)

### 5.1 Copy konfigurasi Nginx
```bash
sudo cp /var/www/ai_data_portal/deploy/nginx.conf /etc/nginx/sites-available/ai-data-portal
```

### 5.2 Edit domain (WAJIB!)
```bash
sudo nano /etc/nginx/sites-available/ai-data-portal
```
Ganti `your-domain.com` dengan domain asli Anda.

### 5.3 Aktifkan site
```bash
sudo ln -s /etc/nginx/sites-available/ai-data-portal /etc/nginx/sites-enabled/
sudo nginx -t                    # Test konfigurasi
sudo systemctl reload nginx      # Reload nginx
```

---

## Langkah 6: Setup SSL (HTTPS) - GRATIS

### 6.1 Pastikan domain sudah pointing ke IP VPS
- Login ke DNS provider (Cloudflare, Namecheap, dll)
- Tambah A record: `your-domain.com` -> `IP_VPS`
- Tunggu propagasi (5-30 menit)

### 6.2 Install SSL dengan Certbot
```bash
sudo certbot --nginx -d your-domain.com
```

### 6.3 Ikuti instruksi:
- Masukkan email
- Agree terms
- Pilih redirect HTTP ke HTTPS (recommended)

### 6.4 Test auto-renewal
```bash
sudo certbot renew --dry-run
```

---

## Langkah 7: Setup Environment Variables

### 7.1 Buat file .env
```bash
nano /var/www/ai_data_portal/.env
```

### 7.2 Isi dengan:
```
ANTHROPIC_API_KEY=sk-ant-xxxxx-your-api-key
```

### 7.3 Pastikan .env tidak ter-commit ke git
```bash
echo ".env" >> /var/www/ai_data_portal/.gitignore
```

---

## Langkah 8: Verifikasi

### 8.1 Cek semua service berjalan
```bash
sudo systemctl status ai-data-portal   # Harus active
sudo systemctl status nginx            # Harus active
```

### 8.2 Buka di browser
```
https://your-domain.com
```

---

## Troubleshooting

### Aplikasi tidak jalan
```bash
# Cek log aplikasi
sudo journalctl -u ai-data-portal -f

# Restart aplikasi
sudo systemctl restart ai-data-portal
```

### Nginx error
```bash
# Test konfigurasi
sudo nginx -t

# Cek log nginx
sudo tail -f /var/log/nginx/error.log
```

### Port 8501 sudah dipakai
```bash
# Cek proses yang pakai port
sudo lsof -i :8501

# Kill proses
sudo kill -9 PID_NUMBER
```

### SSL tidak bisa diinstall
- Pastikan domain sudah pointing ke IP VPS
- Pastikan port 80 dan 443 tidak diblokir firewall
```bash
sudo ufw allow 80
sudo ufw allow 443
```

---

## Maintenance

### Update aplikasi
```bash
cd /var/www/ai_data_portal
git pull origin main              # Jika pakai git
source venv/bin/activate
pip install -r requirements.txt   # Jika ada dependency baru
sudo systemctl restart ai-data-portal
```

### Backup data
```bash
# Backup folder uploads dan data
tar -czvf backup-$(date +%Y%m%d).tar.gz /var/www/ai_data_portal/uploads /var/www/ai_data_portal/data
```

### Monitor resource
```bash
htop                              # CPU & RAM usage
df -h                             # Disk usage
```

---

## Quick Install (Untuk yang sudah familiar)

```bash
# One-liner install (jalankan sebagai root)
curl -sSL https://raw.githubusercontent.com/your-repo/ai_data_portal/main/deploy/install.sh | bash
```

---

## Kontak Support

Jika ada masalah, hubungi:
- Email: admin@company.com
- Telegram: @admin_support

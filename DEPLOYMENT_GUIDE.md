# 🚀 MANDI EAR™ Deployment Guide

## 🌐 **Deploy on Your Website**

This guide helps you deploy MANDI EAR™ on your own website or server.

## 📋 **Requirements**

### **Minimum System Requirements:**
- **OS**: Windows, macOS, or Linux
- **Python**: 3.7 or higher
- **RAM**: 512MB minimum, 1GB recommended
- **Storage**: 100MB for application + dependencies
- **Network**: Internet connection for initial setup

### **Software Requirements:**
- **Python 3.7+** - [Download here](https://python.org/downloads)
- **Web Browser** - Chrome, Firefox, Safari, or Edge
- **Text Editor** (optional) - VS Code, Notepad++, or any editor

## 🖥️ **Local Development Setup**

### **Step 1: Download the Project**
```bash
# Option 1: Git Clone (if you have Git)
git clone https://github.com/infrawithshobhit/mandi-ear.git
cd mandi-ear

# Option 2: Download ZIP
# Download from GitHub and extract to a folder
```

### **Step 2: Run Locally**
```bash
# Windows
python standalone_mandi_ear.py

# Mac/Linux
python3 standalone_mandi_ear.py
```

### **Step 3: Access Your Local Site**
Open browser and visit: **http://localhost:8001**

## 🌐 **Deploy to Web Server**

### **Option 1: Shared Hosting (cPanel/Hostinger/GoDaddy)**

#### **Requirements:**
- Python support (most shared hosts support Python)
- SSH access (preferred) or File Manager

#### **Steps:**
1. **Upload Files**
   - Upload `standalone_mandi_ear.py` to your domain folder
   - Upload `QUICK_START.md` and `README.md`

2. **Install Dependencies**
   ```bash
   # Via SSH
   pip install fastapi uvicorn python-multipart requests
   
   # Or let the app auto-install (recommended)
   ```

3. **Configure Port**
   - Edit `standalone_mandi_ear.py`
   - Change port from 8001 to your hosting provider's required port
   - Usually 80 for HTTP or 443 for HTTPS

4. **Start Application**
   ```bash
   python standalone_mandi_ear.py
   ```

### **Option 2: VPS/Cloud Server (DigitalOcean/AWS/Azure)**

#### **Requirements:**
- Ubuntu 20.04+ or CentOS 7+
- Root or sudo access
- Domain name (optional)

#### **Steps:**

1. **Connect to Server**
   ```bash
   ssh root@your-server-ip
   ```

2. **Install Python & Dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip nginx
   
   # CentOS/RHEL
   sudo yum install python3 python3-pip nginx
   ```

3. **Upload Application**
   ```bash
   # Create directory
   mkdir /var/www/mandi-ear
   cd /var/www/mandi-ear
   
   # Upload standalone_mandi_ear.py
   # You can use scp, git clone, or file upload
   ```

4. **Configure Nginx (Optional)**
   ```nginx
   # /etc/nginx/sites-available/mandi-ear
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

5. **Start Application**
   ```bash
   # Run in background
   nohup python3 standalone_mandi_ear.py &
   
   # Or use systemd service (recommended)
   sudo systemctl enable mandi-ear
   sudo systemctl start mandi-ear
   ```

### **Option 3: Heroku Deployment**

#### **Requirements:**
- Heroku account (free tier available)
- Git installed

#### **Steps:**

1. **Create Heroku App**
   ```bash
   # Install Heroku CLI
   # Create new app
   heroku create your-mandi-ear-app
   ```

2. **Create Required Files**
   
   **Procfile:**
   ```
   web: python standalone_mandi_ear.py
   ```
   
   **requirements.txt:**
   ```
   fastapi==0.104.1
   uvicorn[standard]==0.24.0
   python-multipart==0.0.6
   requests==2.31.0
   ```
   
   **runtime.txt:**
   ```
   python-3.9.18
   ```

3. **Deploy**
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

4. **Access Your App**
   ```
   https://your-mandi-ear-app.herokuapp.com
   ```

### **Option 4: Docker Deployment**

#### **Requirements:**
- Docker installed
- Docker Compose (optional)

#### **Steps:**

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   COPY standalone_mandi_ear.py .
   
   RUN pip install fastapi uvicorn python-multipart requests
   
   EXPOSE 8001
   
   CMD ["python", "standalone_mandi_ear.py"]
   ```

2. **Build & Run**
   ```bash
   # Build image
   docker build -t mandi-ear .
   
   # Run container
   docker run -p 8001:8001 mandi-ear
   ```

3. **Access Application**
   ```
   http://localhost:8001
   ```

## 🔧 **Configuration Options**

### **Change Port**
Edit `standalone_mandi_ear.py`, find this line:
```python
uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
```
Change `8001` to your desired port.

### **Change Host**
For production, you might want to change:
```python
uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
```
- `host="0.0.0.0"` - Accept connections from any IP
- `host="127.0.0.1"` - Only local connections

### **Enable HTTPS**
For production with SSL:
```python
uvicorn.run(app, host="0.0.0.0", port=443, 
           ssl_keyfile="path/to/key.pem",
           ssl_certfile="path/to/cert.pem")
```

## 🚨 **Troubleshooting**

### **Common Issues:**

#### **1. Port Already in Use**
```bash
# Find what's using the port
netstat -tulpn | grep :8001

# Kill the process
sudo kill -9 <process-id>
```

#### **2. Permission Denied**
```bash
# Run with sudo (Linux/Mac)
sudo python3 standalone_mandi_ear.py

# Or change port to > 1024
```

#### **3. Dependencies Not Installing**
```bash
# Update pip
pip install --upgrade pip

# Install manually
pip install fastapi uvicorn python-multipart requests
```

#### **4. Firewall Issues**
```bash
# Ubuntu/Debian
sudo ufw allow 8001

# CentOS/RHEL
sudo firewall-cmd --add-port=8001/tcp --permanent
sudo firewall-cmd --reload
```

## 📊 **Performance Optimization**

### **For Production:**

1. **Use Gunicorn** (instead of Uvicorn)
   ```bash
   pip install gunicorn
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker standalone_mandi_ear:app
   ```

2. **Enable Caching**
   - Add Redis for caching
   - Enable browser caching

3. **Use CDN**
   - Serve static files via CDN
   - Use CloudFlare or similar

4. **Monitor Performance**
   - Add logging
   - Monitor resource usage

## 🔒 **Security Considerations**

### **For Production Deployment:**

1. **Use HTTPS**
   - Get SSL certificate (Let's Encrypt is free)
   - Force HTTPS redirects

2. **Environment Variables**
   - Don't hardcode sensitive data
   - Use environment variables

3. **Firewall**
   - Only open necessary ports
   - Use fail2ban for SSH protection

4. **Updates**
   - Keep Python and dependencies updated
   - Monitor security advisories

## 📞 **Support**

If you need help with deployment:

1. **Check the logs** - Look for error messages in console
2. **Verify requirements** - Ensure Python 3.7+ is installed
3. **Test locally first** - Make sure it works on your computer
4. **Check firewall** - Ensure ports are open
5. **Contact support** - Create an issue on GitHub

## 🎯 **Success Checklist**

- ✅ Python 3.7+ installed
- ✅ Dependencies installed (auto or manual)
- ✅ Application starts without errors
- ✅ Can access via browser
- ✅ All features working (test buttons)
- ✅ Firewall configured (if needed)
- ✅ Domain pointing to server (if using domain)
- ✅ SSL certificate installed (for production)

---

**Your MANDI EAR™ platform is now ready to serve farmers across India!** 🌾🚀
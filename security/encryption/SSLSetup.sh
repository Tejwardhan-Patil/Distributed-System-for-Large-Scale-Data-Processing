#!/bin/bash

# Variables
DOMAIN="website.com"
SSL_DIR="/ssl/$DOMAIN"
CERT_KEY="$SSL_DIR/$DOMAIN.key"
CERT_CSR="$SSL_DIR/$DOMAIN.csr"
CERT_CRT="$SSL_DIR/$DOMAIN.crt"
DAYS_VALID=365
CERT_CA="$SSL_DIR/ca-bundle.crt"

# Function to create SSL directory
create_ssl_directory() {
    if [ ! -d "$SSL_DIR" ]; then
        mkdir -p "$SSL_DIR"
        echo "SSL directory created: $SSL_DIR"
    else
        echo "SSL directory already exists: $SSL_DIR"
    fi
}

# Function to generate private key and CSR
generate_ssl_key_csr() {
    openssl req -newkey rsa:2048 -nodes -keyout "$CERT_KEY" -out "$CERT_CSR" \
        -subj "/C=US/ST=State/L=City/O=Company Name/OU=Org Unit/CN=$DOMAIN"
    
    echo "Private key and CSR generated."
    echo "Private Key: $CERT_KEY"
    echo "CSR: $CERT_CSR"
}

# Function to generate a self-signed certificate
generate_self_signed_cert() {
    openssl x509 -signkey "$CERT_KEY" -in "$CERT_CSR" -req -days "$DAYS_VALID" -out "$CERT_CRT"
    
    echo "Self-signed certificate generated."
    echo "Certificate: $CERT_CRT"
}

# Function to set permissions for SSL directory
set_permissions() {
    chmod 600 "$SSL_DIR"/*
    echo "Permissions set for SSL directory and files."
}

# Function to verify the generated certificate
verify_certificate() {
    openssl x509 -in "$CERT_CRT" -text -noout
    echo "Certificate verification complete."
}

# Function to configure Nginx SSL
configure_nginx_ssl() {
    NGINX_CONF="/nginx/sites-available/$DOMAIN"
    echo "Configuring Nginx for SSL..."

    cat > "$NGINX_CONF" << EOL
server {
    listen 443 ssl;
    server_name $DOMAIN;

    ssl_certificate $CERT_CRT;
    ssl_certificate_key $CERT_KEY;
    ssl_trusted_certificate $CERT_CA;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://127.0.0.1:8080;
    }
}
EOL

    echo "Nginx SSL configuration complete: $NGINX_CONF"
}

# Main execution starts here
create_ssl_directory
generate_ssl_key_csr
generate_self_signed_cert
set_permissions
verify_certificate
configure_nginx_ssl

# Reload Nginx to apply changes
systemctl reload nginx
echo "Nginx reloaded with new SSL settings."
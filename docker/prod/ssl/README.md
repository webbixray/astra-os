# SSL Certificate Placeholder
# Replace with actual certificates for production deployment
#
# For production:
# 1. Obtain valid TLS certificates (Let's Encrypt, DigiCert, etc.)
# 2. Place cert.pem and key.pem in this directory
# 3. Ensure proper permissions: chmod 600 key.pem
#
# For development/testing with mkcert:
#   mkcert -install
#   mkcert -cert-file cert.pem -key-file key.pem "*.astra.local" localhost 127.0.0.1 ::1
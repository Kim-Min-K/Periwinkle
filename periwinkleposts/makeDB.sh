#!/bin/bash

if ! command -v psql &> /dev/null; then
    echo "ERROR: Install Postgres"
    exit 1
fi

read -p "Enter database name: " DB_NAME
read -p "Enter database username: " DB_USER
read -s -p "Enter database password: " DB_PASS
echo

# Create database and user
sudo -u postgres psql <<EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';
ALTER ROLE $DB_USER SET client_encoding TO 'utf8';
ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';
ALTER ROLE $DB_USER SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
ALTER DATABASE $DB_NAME OWNER TO $DB_USER;
EOF

SETTINGS_FILE="periwinkleposts/settings.py" 

ENV_FILE="../.env"

cat > "$ENV_FILE" <<EOL
POSTGRES_DB=$DB_NAME
POSTGRES_USER=$DB_USER
POSTGRES_PASSWORD=$DB_PASS
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
EOL


sed -i "/DATABASES = {/,/}/ {
    s/'NAME':.*/'NAME': '$DB_NAME',/
    s/'USER':.*/'USER': '$DB_USER',/
    s/'PASSWORD':.*/'PASSWORD': '$DB_PASS',/
    s/'HOST':.*/'HOST': 'localhost',/
    s/'PORT':.*/'PORT': '5432',/
}" $SETTINGS_FILE
echo "Updated settings.py"

python manage.py migrate

echo "Credentials:"
echo "Database Name: $DB_NAME"
echo "User: $DB_USER"
echo "Pass: $DB_PASS"
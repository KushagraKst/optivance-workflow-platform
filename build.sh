#!/usr/bin/env bash
# Render Build Script
set -o errexit

pip install -r requirements.txt

# Initialize the database (creates tables + admin user)
python models/db.py

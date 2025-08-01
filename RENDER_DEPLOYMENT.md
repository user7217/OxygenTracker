# Oxygen Cylinder Tracker - Render Deployment Guide

## Overview
This guide covers deploying the Oxygen Cylinder Tracker to Render with PostgreSQL database.

## Prerequisites
- Render account (free tier available)
- GitHub repository with your code
- PostgreSQL database (Render provides this)

## Deployment Steps

### 1. Database Setup
Create a PostgreSQL database on Render:
- Go to Render Dashboard → New → PostgreSQL
- Name: `oxygen-tracker-db`
- User: `oxygen_user` 
- Database: `oxygen_tracker`
- Plan: Starter (free tier)
- Region: Choose closest to your users

### 2. Web Service Setup
Create a web service on Render:
- Go to Render Dashboard → New → Web Service
- Connect your GitHub repository
- Name: `oxygen-cylinder-tracker`
- Environment: `Python 3`
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 main:app`

### 3. Environment Variables
Add these environment variables in Render:

#### Required Variables:
- `DATABASE_URL`: Connection string from your PostgreSQL database
- `SESSION_SECRET`: Generate a secure random string (32+ characters)

#### Optional Variables:
- `SENDGRID_API_KEY`: For email functionality (if using SendGrid)

### 4. Database Connection
The `DATABASE_URL` format for Render PostgreSQL:
```
postgresql://username:password@host:port/database
```

### 5. Application Configuration
The application is configured for PostgreSQL and will:
- Automatically create database tables on first run
- Handle database migrations
- Support user authentication and role-based access

### 6. Post-Deployment Setup
After successful deployment:

1. **Create Admin User**: Visit `/login` and create your first admin user
2. **Import Data**: Use the import functionality to migrate existing data
3. **Configure Users**: Set up additional users and roles as needed

## Features Available After Deployment

### Core Functionality:
- Customer management with full CRUD operations
- Cylinder inventory tracking and rental management
- Bulk operations for cylinder dispatch/return
- Search and filtering across customers and cylinders
- CSV and PDF export capabilities
- Role-based access control (Admin, User, Viewer)

### Data Management:
- PostgreSQL database with robust data integrity
- Automatic backups and data archiving
- Import functionality for existing data migration
- Comprehensive audit trails and rental history

### User Interface:
- Responsive Bootstrap 5 design
- Mobile-optimized touch interface
- Dark theme with professional styling
- Real-time feedback and validation

## Monitoring and Maintenance

### Performance:
- Gunicorn with 2 workers for optimal performance
- Database connection pooling and optimization
- Automatic session management

### Security:
- Secure password hashing with Werkzeug
- Session-based authentication
- Environment variable protection for secrets
- SQL injection protection via SQLAlchemy ORM

## Troubleshooting

### Common Issues:
1. **Database Connection**: Verify `DATABASE_URL` is correctly set
2. **Missing Tables**: Application creates tables automatically on startup
3. **Import Errors**: MS Access import requires additional setup (optional)
4. **Performance**: Monitor worker count and database connections

### Support:
- Check Render logs for detailed error messages
- Database logs available in Render PostgreSQL dashboard
- Application logs show detailed debugging information

## Scaling

### Horizontal Scaling:
- Increase worker count in start command
- Consider upgrading to higher Render plans
- Database read replicas for heavy read workloads

### Database Scaling:
- Render PostgreSQL offers automatic scaling options
- Connection pooling handles concurrent users
- Archiving system manages data growth

## Security Best Practices

1. **Environment Variables**: Never commit secrets to code
2. **Database Access**: Use connection pooling and prepared statements
3. **User Authentication**: Implement strong password policies
4. **Session Management**: Secure session configuration
5. **HTTPS**: Render provides automatic SSL certificates

## Cost Optimization

- Use Render's free tier for development/testing
- PostgreSQL starter plan supports moderate usage
- Monitor usage and scale based on actual needs
- Consider data archiving for long-term storage optimization
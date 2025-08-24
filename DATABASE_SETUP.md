# Database Setup Guide

This guide explains how to connect your application to the MySQL database for the missing persons functionality.

## Database Configuration

The application is configured to connect to your MySQL database with the following details:

- **Host**: sql12.freesqldatabase.com
- **Database**: sql12795688
- **Username**: sql12795688
- **Password**: VATyekp2U8
- **Port**: 3306

## Backend Setup

### 1. Install Dependencies

First, install the required Python packages:

```bash
cd backend
pip install -r requirements.txt
```

### 2. Initialize Database

Run the database initialization script to create the required tables:

```bash
cd backend
python scripts/init_db.py
```

This will create the `missing_persons` table with the following structure:

```sql
CREATE TABLE missing_persons (
  id INT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(120) NOT NULL,
  target_image_url TEXT NOT NULL,
  status VARCHAR(16) DEFAULT 'missing',
  notes TEXT,
  approval VARCHAR(16) NOT NULL DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 3. Start the Backend Server

```bash
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## Frontend Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Start the Frontend

```bash
npm run dev
```

## API Endpoints

The following API endpoints are now available:

- `GET /api/missing-persons` - Get all missing persons
- `GET /api/missing-persons/{id}` - Get a specific missing person
- `POST /api/missing-persons` - Create a new missing person
- `PUT /api/missing-persons/{id}` - Update a missing person
- `DELETE /api/missing-persons/{id}` - Delete a missing person

## Environment Variables (Optional)

You can override the database configuration using environment variables:

```bash
export DB_HOST=your_host
export DB_NAME=your_database
export DB_USER=your_username
export DB_PASSWORD=your_password
export DB_PORT=your_port
```

## Usage

1. **View Missing Persons**: The MissingPeople page will automatically load data from the database
2. **Add New Person**: Click "Add New Missing Person" to create a new entry
3. **Edit Person**: Click on any row to view/edit details
4. **Delete Person**: Use the delete button in the edit modal
5. **Upload Images**: Images are uploaded using the existing target upload endpoint

## Troubleshooting

### Connection Issues
- Verify your database credentials are correct
- Check if the database server is accessible from your network
- Ensure the database exists and the user has proper permissions

### Table Creation Issues
- Run the initialization script manually: `python scripts/init_db.py`
- Check the console output for any error messages
- Verify the database user has CREATE TABLE permissions

### API Issues
- Check the backend server is running on port 8000
- Verify CORS is properly configured
- Check the browser console for any error messages

## Security Notes

- The database credentials are currently hardcoded in the configuration
- For production use, consider using environment variables or a secure configuration management system
- Ensure proper database user permissions (only necessary operations)
- Consider implementing authentication and authorization for the API endpoints

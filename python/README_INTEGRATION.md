# Obserra CCTV Management - Python Backend Integration

This directory contains the Python backend that integrates with your Flutter CCTV Management page.

## What This Integration Provides

1. **Real-time Camera Management**: Add, edit, delete, and monitor CCTV cameras
2. **Status Updates**: Real-time camera status (Active/Offline) with automatic refresh
3. **Camera Configuration**: Store camera settings like source, resolution, location
4. **RESTful API**: Clean API endpoints for Flutter to communicate with
5. **Data Persistence**: Automatically saves camera data to `cameras.json`

## Quick Start

### 1. Install Python Dependencies

```bash
cd python
pip install -r requirements.txt
```

### 2. Run the Backend

```bash
python simple_api.py
```

The API will start at `http://localhost:8000`

### 3. Test the API

Open your browser and go to `http://localhost:8000/docs` to see the interactive API documentation.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info and available endpoints |
| GET | `/cameras` | List all cameras |
| POST | `/cameras` | Add new camera |
| PUT | `/cameras/{id}` | Update camera |
| DELETE | `/cameras/{id}` | Delete camera |
| GET | `/cameras/{id}/status` | Get camera status |
| POST | `/cameras/{id}/toggle` | Toggle camera status |
| GET | `/health` | Health check |

## Flutter Integration

Your Flutter app (`cctvmanagement.dart`) is now configured to:

- **Fetch cameras** from the Python backend
- **Add new cameras** through a dialog form
- **Toggle camera status** (Active/Offline)
- **View camera settings** in a details dialog
- **Auto-refresh** every 10 seconds
- **Filter cameras** by status (All/Active/Offline)

## Data Flow

1. **Flutter** → **Python API** → **cameras.json**
2. **Real-time updates** every 10 seconds
3. **Fallback to mock data** if API is unavailable
4. **Automatic data persistence** to JSON file

## Configuration

### Camera Data Structure

```json
{
  "id": "CAM-001",
  "name": "Camera Name",
  "location": "Gate A",
  "status": "Active",
  "last_updated": "2025-01-27T10:30:00",
  "source": "0",
  "width": 640,
  "height": 480
}
```

### Source Types

- **Webcam**: Use `"0"` for default webcam
- **IP Camera**: Use RTSP URL like `"rtsp://user:pass@ip:port/stream"`

## Troubleshooting

### Common Issues

1. **Port 8000 already in use**
   - Change port in `simple_api.py` line 200
   - Update Flutter `baseUrl` in `cctvmanagement.dart`

2. **CORS errors**
   - Backend already has CORS enabled for all origins
   - Check if firewall is blocking the connection

3. **Flutter can't connect**
   - Ensure Python backend is running
   - Check if `localhost:8000` is accessible
   - Verify network permissions on mobile devices

### Debug Mode

The backend runs with `reload=True` for development. Check the console for:
- Camera loading status
- API request logs
- Error messages

## Next Steps

1. **Run the backend**: `python simple_api.py`
2. **Test in Flutter**: Navigate to CCTV Management page
3. **Add cameras**: Use the "Add New Camera" button
4. **Monitor status**: Watch real-time updates
5. **Customize**: Modify camera settings and add more features

## Integration Benefits

✅ **Stateful Flutter UI** - Real-time data updates  
✅ **Python Backend** - Robust camera management  
✅ **Data Persistence** - Automatic JSON storage  
✅ **Real-time Updates** - 10-second refresh cycle  
✅ **Error Handling** - Fallback to mock data  
✅ **Clean API** - RESTful endpoints  
✅ **CORS Enabled** - Works with web and mobile  

Your Flutter CCTV Management page is now fully integrated with a Python backend! 🎉

# 🚀 How to Run Obserra CCTV Management System

This guide will walk you through running your integrated Flutter + Python CCTV management system step by step.

## 📋 Prerequisites

Before you start, make sure you have:

- ✅ **Python 3.7+** installed on your system
- ✅ **Flutter SDK** installed and configured
- ✅ **Git** (optional, for version control)
- ✅ **Code editor** (VS Code, Android Studio, etc.)

## 🏗️ Project Structure

```
obserra_software/
├── bismillahsukses/          # Main Flutter project
│   ├── lib/                  # Flutter source code
│   │   └── content/
│   │       └── cctvmanagement.dart  # CCTV Management page
│   ├── python/               # Python backend
│   │   ├── simple_api.py     # FastAPI server
│   │   ├── requirements.txt  # Python dependencies
│   │   ├── start_backend.bat # Windows startup script
│   │   └── cameras.json      # Camera data storage
│   └── pubspec.yaml          # Flutter dependencies
└── README.md
```

## 🐍 Step 1: Start the Python Backend

### Option A: Easy Way (Windows)

1. **Navigate to the Python folder:**
   ```bash
   cd bismillahsukses/python
   ```

2. **Double-click `start_backend.bat`**
   
   OR run from command line:
   ```bash
   start_backend.bat
   ```

### Option B: Manual Commands

1. **Open Command Prompt/PowerShell:**
   ```bash
   cd bismillahsukses/python
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the API server:**
   ```bash
   python simple_api.py
   ```

### ✅ What You Should See

```
Starting Obserra CCTV API...
Cameras loaded: 3
API will be available at: http://localhost:8000
Press Ctrl+C to stop
```

## 📱 Step 2: Start the Flutter App

### Option A: VS Code

1. **Open VS Code**
2. **Open the Flutter project folder:** `bismillahsukses`
3. **Press `F5`** or click the "Run" button
4. **Select your target device** (Chrome for web, Android emulator, etc.)

### Option B: Command Line

1. **Open a NEW terminal** (keep Python backend running in the first one)
2. **Navigate to Flutter project:**
   ```bash
   cd bismillahsukses
   ```

3. **Install Flutter dependencies:**
   ```bash
   flutter pub get
   ```

4. **Run the app:**
   ```bash
   flutter run
   ```

5. **Select your target device** when prompted

## 🧪 Step 3: Test the Integration

### 1. Verify Backend is Running

- **Open your browser** and go to: `http://localhost:8000`
- **You should see:** API information and available endpoints
- **API Documentation:** Visit `http://localhost:8000/docs`

### 2. Test Flutter App

1. **Navigate to CCTV Management page** in your Flutter app
2. **You should see:**
   - Real camera data from Python backend
   - Loading indicators
   - Camera status updates
   - Interactive buttons

### 3. Test Features

- ✅ **Add New Camera:** Click "Add New Camera" button
- ✅ **Toggle Status:** Click play/pause buttons on cameras
- ✅ **View Settings:** Click settings icon on cameras
- ✅ **Filter Cameras:** Use All/Active/Offline filter buttons

## 🔧 Troubleshooting

### Common Issues & Solutions

#### 1. **Port 8000 Already in Use**

**Error:** `Address already in use`

**Solution:**
```bash
# Change port in simple_api.py (line 200)
uvicorn.run(
    "simple_api:app",
    host="0.0.0.0",
    port=8001,  # Change from 8000 to 8001
    reload=True,
    log_level="info"
)

# Update Flutter baseUrl in cctvmanagement.dart
final String baseUrl = "http://localhost:8001";  // Change to match
```

#### 2. **Python Dependencies Fail to Install**

**Error:** `pip install` fails

**Solution:**
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v

# Or install individually
pip install fastapi uvicorn pydantic
```

#### 3. **Flutter Can't Connect to Backend**

**Error:** Connection refused or timeout

**Solution:**
1. **Check if backend is running:**
   ```bash
   # In browser: http://localhost:8000
   # Should show API info
   ```

2. **Check firewall settings**
3. **Verify baseUrl in Flutter code**
4. **Try different port if needed**

#### 4. **Flutter Dependencies Missing**

**Error:** `http` package not found

**Solution:**
```bash
cd bismillahsukses
flutter pub get
flutter clean
flutter pub get
```

#### 5. **Camera Data Not Loading**

**Error:** Empty camera list or mock data

**Solution:**
1. **Check Python backend console** for errors
2. **Verify cameras.json exists** in python folder
3. **Check network permissions** on mobile devices
4. **Test API endpoint:** `http://localhost:8000/cameras`

## 📊 API Endpoints Reference

| Method | Endpoint | Description | Test URL |
|--------|----------|-------------|----------|
| GET | `/` | API info | `http://localhost:8000/` |
| GET | `/cameras` | List cameras | `http://localhost:8000/cameras` |
| POST | `/cameras` | Add camera | Use Postman/curl |
| PUT | `/cameras/{id}` | Update camera | Use Postman/curl |
| DELETE | `/cameras/{id}` | Delete camera | Use Postman/curl |
| GET | `/health` | Health check | `http://localhost:8000/health` |

## 🎯 Quick Start Commands

### **Complete Setup (Copy & Paste)**

```bash
# Terminal 1: Start Python Backend
cd bismillahsukses/python
pip install -r requirements.txt
python simple_api.py

# Terminal 2: Start Flutter App
cd bismillahsukses
flutter pub get
flutter run
```

### **Windows Quick Start**

```bash
# Terminal 1: Start Backend
cd bismillahsukses/python
start_backend.bat

# Terminal 2: Start Flutter
cd bismillahsukses
flutter run
```

## 🔍 Debug Mode

### **Python Backend Debug**

The backend runs with `reload=True` for development. Check console for:
- Camera loading status
- API request logs
- Error messages
- Database operations

### **Flutter Debug**

1. **Open DevTools** in VS Code or browser
2. **Check Network tab** for API calls
3. **View console logs** for errors
4. **Use Flutter Inspector** for UI debugging

## 📱 Platform-Specific Notes

### **Web (Chrome)**
- Works best with localhost
- CORS is already configured
- No additional setup needed

### **Android Emulator**
- Use `10.0.2.2:8000` instead of `localhost:8000`
- Update `baseUrl` in Flutter code:
  ```dart
  final String baseUrl = "http://10.0.2.2:8000";
  ```

### **iOS Simulator**
- Use `localhost:8000` (same as web)
- No additional setup needed

### **Physical Device**
- Use your computer's IP address
- Update `baseUrl` in Flutter code:
  ```dart
  final String baseUrl = "http://192.168.1.100:8000";  // Your PC's IP
  ```

## 🎉 Success Indicators

You'll know everything is working when:

1. ✅ **Python backend shows:** "API will be available at http://localhost:8000"
2. ✅ **Browser can access:** `http://localhost:8000`
3. ✅ **Flutter app shows:** Real camera data (not mock data)
4. ✅ **Add Camera button works** and shows success message
5. ✅ **Camera status toggles** work and update in real-time
6. ✅ **Filter buttons** show different camera lists

## 🆘 Getting Help

### **Check These First:**
1. Is Python backend running? (Check terminal)
2. Can you access `http://localhost:8000` in browser?
3. Are there any error messages in terminals?
4. Did you run `flutter pub get`?

### **Common Success Path:**
1. ✅ Start Python backend → See "API available" message
2. ✅ Test in browser → Can access localhost:8000
3. ✅ Start Flutter app → Navigate to CCTV Management
4. ✅ See real camera data → Integration successful!

---

## 🚀 **Ready to Run!**

You now have everything you need to run your integrated CCTV management system. Start with Step 1 (Python backend) and work your way through. The system is designed to be robust with fallbacks, so even if something goes wrong, you'll still see mock data in Flutter.

**Happy coding! 🎉**

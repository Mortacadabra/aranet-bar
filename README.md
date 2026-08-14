# AranetBar

A lightweight GNOME top-bar monitor for **Aranet4** environmental sensors on Ubuntu.

AranetBar connects to an Aranet4 over Bluetooth Low Energy (BLE), periodically retrieves environmental measurements, displays the latest CO₂ reading in the GNOME top bar, and stores historical measurements in CSV format.

## Features

- CO₂ monitoring
- Temperature monitoring
- Relative humidity monitoring
- Atmospheric pressure monitoring
- GNOME top-bar indicator
- Bluetooth Low Energy (BLE)
- Automatic CSV logging
- 10-minute sampling interval
- Manual refresh
- Automatic startup after Ubuntu login
- Keeps the last successful reading displayed between measurements
- Prevents multiple instances from running simultaneously

## Requirements

- Ubuntu with GNOME
- Python3
- Bluetooth / BLE support
- Aranet4 sensor

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/ADIIIB/aranet-bar.git
cd aranet-bar
```

### 2. Install Ubuntu dependencies

```bash
sudo apt update

sudo apt install \
    python3 \
    python3-venv \
    python3-gi \
    gir1.2-gtk-3.0 \
    gir1.2-ayatanaappindicator3-0.1 \
    bluez
```

### 3. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

## Pair Your Aranet4

Start the Bluetooth command-line utility:

```bash
bluetoothctl
```

Enable the Bluetooth agent:

```text
agent on
default-agent
scan on
```

Wait for your Aranet4 to appear, then list discovered devices:

```text
devices
```

You should see something similar to:

```text
Device XX:XX:XX:XX:XX:XX Aranet4
```

Pair the device:

```text
pair XX:XX:XX:XX:XX:XX
```

Your Aranet4 may display a pairing code on its screen.

Enter that code when Ubuntu requests it.

Then trust the device:

```text
trust XX:XX:XX:XX:XX:XX
```

Stop scanning:

```text
scan off
```

Exit:

```text
exit
```

## Configuration

Open `main.py` and set the Bluetooth MAC address of your Aranet4:

```python
ARANET_MAC = "XX:XX:XX:XX:XX:XX"
```

The default sampling interval is **10 minutes**:

```python
REFRESH_INTERVAL = 600
```

The interval is specified in seconds.

For example:

```text
300  = 5 minutes
600  = 10 minutes
1800 = 30 minutes
```

## Run AranetBar

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Run:

```bash
python main.py
```

After a successful reading, the current CO₂ level appears in the GNOME top bar:

```text
🟢 519 ppm
```

AranetBar keeps the latest successful value displayed until a newer measurement is available.

The application does **not** continuously query the sensor.

By default:

```text
Read Aranet4
      ↓
Display reading
      ↓
Save reading to CSV
      ↓
Wait 10 minutes
      ↓
Read again
```

## CO₂ Indicator

The top-bar indicator uses three ranges:

| CO₂ | Indicator |
| --- | --- |
| Below 800 ppm | 🟢 |
| 800–1199 ppm | 🟡 |
| 1200 ppm and above | 🔴 |

Click the indicator to view additional sensor information and access:

- CO₂
- Temperature
- Relative humidity
- Atmospheric pressure
- Last update time
- Refresh now
- Quit

## Data Logging

Every successful measurement is automatically appended to a CSV file.

By default, the history file is stored at:

```text
~/Aranet4/aranet4_history.csv
```

Recorded fields include:

```text
Date/Time
CO₂ (ppm)
Temperature (°C)
Relative Humidity (%)
Atmospheric Pressure (hPa)
```

Example:

```csv
DateTime,CO2_ppm,Temperature_C,Relative_Humidity_percent,Atmospheric_Pressure_hPa
2025-01-01 18:00:03,719,24.1,55,1016.2
2025-01-01 18:10:03,727,24.2,55,1016.1
2025-01-01 18:20:03,741,24.3,56,1016.0
```

Only successful sensor readings are written to the CSV file.

If a Bluetooth request fails, AranetBar keeps displaying the last successful CO₂ value.

## Start Automatically with Ubuntu

AranetBar can launch automatically when you log into Ubuntu.

### 1. Create the autostart directory

```bash
mkdir -p ~/.config/autostart
```

### 2. Create an autostart entry

```bash
nano ~/.config/autostart/aranet-bar.desktop
```

Add:

```ini
[Desktop Entry]
Type=Application
Name=AranetBar
Comment=Aranet4 environmental monitor
Exec=sh -c "sleep 30; /FULL/PATH/TO/aranet-bar/.venv/bin/python /FULL/PATH/TO/aranet-bar/main.py"
Terminal=false
X-GNOME-Autostart-enabled=true
```

Replace:

```text
/FULL/PATH/TO/aranet-bar
```

with the actual location of the cloned repository.

For example:

```ini
Exec=sh -c "sleep 30; /home/username/aranet-bar/.venv/bin/python /home/username/aranet-bar/main.py"
```

The 30-second delay gives Ubuntu and Bluetooth time to initialize after login.

Save the file in Nano:

```text
Ctrl + O
Enter
Ctrl + X
```

Make the autostart entry executable:

```bash
chmod +x ~/.config/autostart/aranet-bar.desktop
```

Log out and back in, or reboot Ubuntu.

AranetBar should then launch automatically after login.

No terminal window needs to remain open.

## Check the Background Process

Find the running AranetBar process:

```bash
pgrep -af '/aranet-bar/main.py'
```

Example:

```text
5979 /home/username/aranet-bar/.venv/bin/python /home/username/aranet-bar/main.py
```

The first number is the process ID (PID).

View CPU and memory usage:

```bash
ps -p PID -o pid,ppid,%cpu,%mem,rss,vsz,etime,cmd
```

Replace `PID` with the actual process ID.

For live monitoring:

```bash
top -p PID
```

or:

```bash
htop
```

## Stop AranetBar

Use the **Quit** option from the top-bar menu.

Alternatively:

```bash
pkill -f '/aranet-bar/main.py'
```

If AranetBar is configured to start automatically, quitting it will stop it for the current login session. It will start again the next time the autostart entry is executed.

## Troubleshooting

### Aranet4 is not discovered

Check that Bluetooth is enabled:

```bash
bluetoothctl show
```

Then scan:

```bash
bluetoothctl
scan on
```

Make sure the Aranet4 is nearby and Bluetooth is enabled on the sensor.

### Authentication or pairing errors

Remove the existing Bluetooth pairing:

```bash
bluetoothctl
remove XX:XX:XX:XX:XX:XX
```

Then pair the Aranet4 again and enter the pairing code displayed on the device.

### `CO₂ error` appears

Make sure:

- The Aranet4 is powered on
- Bluetooth is enabled
- The configured MAC address is correct
- The device has been paired successfully
- Another application is not currently communicating with the Aranet4

Temporary BLE/GATT errors may occur. AranetBar keeps the previous successful measurement displayed when possible and will try again at the next sampling interval.

### Multiple indicators

AranetBar uses a process lock to prevent multiple instances from running simultaneously.

If necessary, stop existing instances:

```bash
pkill -f '/aranet-bar/main.py'
```

Then start AranetBar again.

## Project Structure

```text
aranet-bar/
├── main.py
├── README.md
├── requirements.txt
├── .gitignore
└── LICENSE
```

Do not commit your virtual environment or measurement history.

A recommended `.gitignore` includes:

```gitignore
.venv/
.idea/
__pycache__/
*.pyc
*.csv
```

## License

AranetBar is licensed under the **MIT License**.
See the `LICENSE` file for details.
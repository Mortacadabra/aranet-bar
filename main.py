import gi
import csv
import sys
import fcntl
import aranet4
from datetime import datetime
from pathlib import Path
from gi.repository import Gtk, GLib, AyatanaAppIndicator3

gi.require_version("Gtk", "3.0")
gi.require_version("AyatanaAppIndicator3", "0.1")


# CONFIG

ARANET_MAC = "Enter your Aranet MAC address"

# 10 minutes = 600 seconds
REFRESH_INTERVAL = 600

# CSV log file
CSV_FILE = Path.home() / "Aranet4" / "aranet4_history.csv"

# Prevent multiple copies of the app from running
LOCK_FILE = "/tmp/aranet-co2-indicator.lock"



# SINGLE-INSTANCE LOCK
lock_handle = open(LOCK_FILE, "w")

try:
    fcntl.flock(
        lock_handle,
        fcntl.LOCK_EX | fcntl.LOCK_NB
    )

except BlockingIOError:
    print("Aranet CO₂ indicator is already running.")
    sys.exit(0)




class AranetIndicator:

    def __init__(self):

        # Last successful values
        self.last_co2 = None
        self.last_temperature = None
        self.last_humidity = None
        self.last_pressure = None
        self.last_update_time = None


        # TOP-BAR INDICATOR
        self.indicator = AyatanaAppIndicator3.Indicator.new(
            "aranet-co2",
            "weather-clear-symbolic",
            AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )

        self.indicator.set_status(
            AyatanaAppIndicator3.IndicatorStatus.ACTIVE
        )

        self.indicator.set_label(
            "CO₂ connecting...",
            ""
        )


        # MENU
        menu = Gtk.Menu()

        self.co2_item = Gtk.MenuItem(
            label="CO₂: waiting for first reading..."
        )
        self.co2_item.set_sensitive(False)
        menu.append(self.co2_item)

        self.temperature_item = Gtk.MenuItem(
            label="Temperature: --"
        )
        self.temperature_item.set_sensitive(False)
        menu.append(self.temperature_item)

        self.humidity_item = Gtk.MenuItem(
            label="Humidity: --"
        )
        self.humidity_item.set_sensitive(False)
        menu.append(self.humidity_item)

        self.pressure_item = Gtk.MenuItem(
            label="Pressure: --"
        )
        self.pressure_item.set_sensitive(False)
        menu.append(self.pressure_item)

        self.last_update_item = Gtk.MenuItem(
            label="Last update: --"
        )
        self.last_update_item.set_sensitive(False)
        menu.append(self.last_update_item)

        # Separator
        menu.append(Gtk.SeparatorMenuItem())

        # Refresh now
        refresh_item = Gtk.MenuItem(
            label="Refresh now"
        )

        refresh_item.connect(
            "activate",
            self.manual_refresh
        )

        menu.append(refresh_item)

        # Quit
        quit_item = Gtk.MenuItem(
            label="Quit"
        )

        quit_item.connect(
            "activate",
            self.quit_app
        )

        menu.append(quit_item)

        menu.show_all()

        self.indicator.set_menu(menu)

        # FIRST READING
        # Wait 3 seconds after launch
        GLib.timeout_add_seconds(
            3,
            self.first_refresh
        )

    # FIRST REFRESH
    def first_refresh(self):

        self.refresh()

        # After the first reading,
        # read again every 10 minutes
        GLib.timeout_add_seconds(
            REFRESH_INTERVAL,
            self.refresh
        )

        # False = do not repeat this 3-second timer
        return False


    # READ ARANET4
    def read_aranet(self):

        try:

            print("Checking Aranet4...")

            reading = aranet4.client.get_current_readings(
                ARANET_MAC
            )

            if reading.co2 is None or reading.co2 <= 0:
                raise ValueError(
                    "Invalid CO₂ reading"
                )

            return reading

        except Exception as e:

            print(
                "ARANET ERROR:",
                repr(e)
            )

            return None


    # SAVE READING TO CSV
    def save_to_csv(self, reading):

        try:

            # Create ~/Aranet4 if it doesn't exist
            CSV_FILE.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            file_exists = CSV_FILE.exists()

            with open(
                CSV_FILE,
                "a",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.writer(file)

                # Write header only for a new file
                if not file_exists or CSV_FILE.stat().st_size == 0:

                    writer.writerow([
                        "DateTime",
                        "CO2_ppm",
                        "Temperature_C",
                        "Relative_Humidity_percent",
                        "Atmospheric_Pressure_hPa"
                    ])

                writer.writerow([
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    reading.co2,
                    reading.temperature,
                    reading.humidity,
                    reading.pressure
                ])

            print(
                f"Saved reading to: {CSV_FILE}"
            )

        except Exception as e:

            print(
                "CSV ERROR:",
                repr(e)
            )

    # REFRESH
    def refresh(self):

        reading = self.read_aranet()

        # SUCCESSFUL READING
        if reading is not None:

            self.last_co2 = reading.co2
            self.last_temperature = reading.temperature
            self.last_humidity = reading.humidity
            self.last_pressure = reading.pressure
            self.last_update_time = datetime.now()

            # Save to CSV
            self.save_to_csv(reading)

            # Choose CO₂ indicator
            if self.last_co2 < 800:

                symbol = "🟢"

            elif self.last_co2 < 1200:

                symbol = "🟡"

            else:

                symbol = "🔴"

            # Top bar
            self.indicator.set_label(
                f"{symbol} {self.last_co2} ppm",
                ""
            )

            # Menu information
            self.co2_item.set_label(
                f"CO₂: {self.last_co2} ppm"
            )

            self.temperature_item.set_label(
                f"Temperature: "
                f"{self.last_temperature} °C"
            )

            self.humidity_item.set_label(
                f"Humidity: "
                f"{self.last_humidity}%"
            )

            self.pressure_item.set_label(
                f"Pressure: "
                f"{self.last_pressure} hPa"
            )

            self.last_update_item.set_label(
                "Last update: "
                + self.last_update_time.strftime(
                    "%m/%d/%Y %I:%M:%S %p"
                )
            )

            print(
                f"CO₂: {self.last_co2} ppm | "
                f"Temperature: {self.last_temperature} °C | "
                f"Humidity: {self.last_humidity}% | "
                f"Pressure: {self.last_pressure} hPa"
            )

        # FAILED READING
        else:

            # No successful reading has ever occurred
            if self.last_co2 is None:

                self.indicator.set_label(
                    "⚙ CO₂ error",
                    ""
                )

                self.co2_item.set_label(
                    "CO₂: unable to read sensor"
                )

            # We already have an older valid reading
            else:

                print(
                    "Reading failed. "
                    "Keeping previous value:",
                    self.last_co2
                )

                # Do not change the top-bar value
                # It continues showing the last successful CO₂ measurement
                self.co2_item.set_label(
                    f"CO₂: {self.last_co2} ppm "
                    "(last successful reading)"
                )

        # Keeps the 10-minute timer alive
        return True


    # MANUAL REFRESH
    def manual_refresh(self, _):

        print("Manual refresh requested.")

        self.refresh()


    # QUIT
    def quit_app(self, _):

        Gtk.main_quit()

    # RUN
    def run(self):

        Gtk.main()



# START APPLICATION
if __name__ == "__main__":

    app = AranetIndicator()
    app.run()


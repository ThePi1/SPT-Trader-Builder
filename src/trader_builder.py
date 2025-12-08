import csv, json, os, sys, traceback, datetime, ctypes, time
import requests
from os import path
from pathlib import Path
from gui import Gui_MainWindow, Gui_QuestDlg
from configparser import ConfigParser
from PyQt6.QtWidgets import QApplication, QDialog, QMainWindow, QPushButton, QHeaderView

# Parse string to boolean
def is_true(val):
  val = val.lower()
  if val in ('y', 'yes', 't', 'true', 'on', '1'):
    return True
  elif val in ('n', 'no', 'f', 'false', 'off', '0'):
    return False
  else:
    raise ValueError("invalid truth value %r" % (val,))

# Set up config parser and read in the settings file
parser = ConfigParser()
base_path = Path(__file__).parent
parser.read('data/settings.ini')

# The controller holds most of the data and methods used to calculate trades.
class Controller:
  # Parse the settings.ini file for the following settings
  try:
    version_file                          = str(parser.get('filepaths', "version_file"))
    version_url                           = str(parser.get('filepaths', 'version_url'))
    project_url                           = str(parser.get('filepaths', 'project_url'))

  except Exception as e:
    print(f"Error loading settings.ini file. Please check the exception below and the corresponding entry in the settings file.\nMost likely, the format for your entry is off. Check the top of settings.ini for more info.\n\n{traceback.format_exc()}")
    exit()

  def get_version_from_file():
    with open(Controller.version_file) as local_version_file:
      local_version = local_version_file.read()
      return local_version
    
  def get_version_from_remote():
    try:
      latest_version = requests.get(Controller.version_url).text
      return latest_version
    except Exception as e:
      print("Error fetching remote version")
      return ''

  def check_version():
    try:
      print("Checking version...\n")
      latest_version = Controller.get_version_from_remote()
      local_version = Controller.get_version_from_file()
      if local_version != latest_version:
        print(f"Version {local_version} may be out of date!\nLatest version: {latest_version}\n\nPlease visit {Controller.project_url} to download the latest version.")
        print("Or, if running from source, please pull the latest changes via 'git pull'")
      else:
        print(f"Version {local_version} is up to date.")
    except Exception as e:
      print(f"Error checking version: {e}")

  # This may get called before everything else gets initialized
  def get_update_stats():
    project_url = str(parser.get('filepaths', 'project_url'))
    latest_version = Controller.get_version_from_remote()
    local_version = Controller.get_version_from_file()
    if local_version != latest_version:
      update_text = "Program may be out of date!"
    else:
      update_text = "Up to date."
    return (local_version, latest_version, update_text, project_url)

def fix_win_taskbar():
  app_id = u'spt-tbt-tool'
  ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

# Main method
def main():
  # Use this on Windows to add the icon back to the taskbar
  # No idea how this works on Mac/Linux for now, haha
  if sys.platform == 'win32':
    fix_win_taskbar()

  # Create the application and main window
  app = QApplication(sys.argv)
  win = Gui_MainWindow()
  ver_current, ver_latest, update_text, project_url = Controller.get_update_stats()

  # # Set up triggers that need specific data
  win.ui.actionAbout.triggered.connect(lambda: Gui_MainWindow.onAbout(win, ver_current, project_url))
  win.ui.actionUpdateCheck.triggered.connect(lambda: Gui_MainWindow.onUpdateWindow(win, ver_current, ver_latest, project_url, update_text))
  win.ui.actionQuest_Builder.triggered.connect(lambda: Gui_MainWindow.onQuestWindow(win))

  win.show()
  # Run the application's main loop
  sys.exit(app.exec())

if __name__ == '__main__':
  main()
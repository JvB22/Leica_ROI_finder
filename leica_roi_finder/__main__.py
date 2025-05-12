import argparse
import os

# Package imports
from leica_roi_finder.gui.gui import roi_finder_gui
import leica_roi_finder

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version=f'Leica ROI finder - version: {leica_roi_finder.__version__}')
    parser.add_argument("--shortcut", action='store_true')

    args = parser.parse_args()

    if args.shortcut:
        try:
            script_path = os.path.abspath(__file__)
            from pyshortcuts import make_shortcut
            
            make_shortcut(
                script_path, 
                name="Leica ROI finder",
                desktop=True,
                startmenu=True
            )
            print("Succesfully created desktop shortcut")
        except Exception as error:
            print(f"Failed to create shortcut:\n{error}")
    else:
        roi_finder_gui()

if __name__=="__main__":
    main()
# viewportCapture for Autodesk Maya
A tool for capturing and managing viewport display settings in Maya. It can generate MEL scripts and presets that let you easily reuse the same settings later. These configurations can be saved to a shelf, assigned to a shortcut, or shared with other users via a network drive. This is especially useful for creating consistent-looking playblasts in previs, layout, and animation, leading to more coherent context edits and reducing viewer distraction.

---
### [Watch how it works on YouTube](https://youtu.be/YzBcwsvm5Ro)
[![Watch the video](https://img.youtube.com/vi/YzBcwsvm5Ro/maxresdefault.jpg)](https://youtu.be/YzBcwsvm5Ro)




---

## Features

-   **Settings Management:** Capture, save, load, and delete viewport display configurations.
-   **MEL Script Generation:** Automatically generate MEL scripts from captured settings for shelf buttons or standalone Mel Scripts.
-   **Team Collaboration:** Share presets via a network drive for consistent visual output across your team.
-   **Customizable Preset Paths:** Define a custom directory for saving and loading presets.
-   **Default Path Fallback:** Automatically uses a default Maya user directory if custom path isn't set or found.
-   **Extensive Attribute Coverage:** Captures a wide range of display attributes, including standard visibility, Hardware 2.0 settings, camera gates, fog, film fit, and background colors, and is continually updated based on user and community feedback.

## Why it's Useful

The Problem: Maya's viewport offers a vast array of display settings. In a fast-paced production environment, where individuals are rightly focused on complex creative and technical challenges, it can happen that these detailed settings are inadvertently overlooked or differ between team members, or even for the same person across different work sessions. For instance, one playblast might be missing textures, another shadows, or a third might not have double-sided lighting active. These aren't necessarily 'mistakes' in the traditional sense, but rather understandable human oversights when juggling numerous priorities. The core issue is that such visual inconsistencies, however they arise, can lead to kickbacks, and consume valuable time and energy that could be better spent on the primary tasks at hand.

viewportCapture addresses these issues by:

-   Ensuring consistent playblasts and viewport setups every time.
-   Facilitating teamwork by allowing presets to be shared, ensuring the entire team uses the same standardized configurations.
-   Speeding up workflows by allowing quick application of complex viewport configurations.
-   Reducing errors and inconsistencies in visual output across a project.
-   Providing a simple way to generate MEL scripts for viewport settings. These scripts can be easily integrated into shelf buttons, hotkeys, custom UIs, or other automated pipeline tools for consistent scene setup.

## Quick Guide: Using viewportCapture

Here’s a brief overview of common tasks you can perform with viewportCapture:

### 1. Capturing Viewport Settings

1.  Ensure the Maya viewport you wish to capture settings from is currently active (click in it).
2.  In the viewportCapture UI, click the **"Capture Active Viewport"** button. The tool will read and display the current display settings as a MEL script.


---

### 2. Generating and Using MEL for Shelf Buttons

1.  ...after capturing settings. (or loading a preset)
2.  Select all the MEL code (Ctrl+A or Cmd+A).
3.  Middle-mouse-drag the selected text directly on your Maya shelf. Maya will prompt you to save it as a MEL or Python script; choose MEL.


---

### 3. Saving and Loading Presets

viewportCapture allows you to save your captured settings as presets for easy reuse. You can also load existing presets.

#### Saving a New Preset:

1.  After capturing the desired viewport settings (see step 1), click the **"Save New Preset"** button in the viewportCapture UI.
2.  A dialog will appear prompting you to enter a name for your preset. Type a descriptive name and click "Save".
3.  The preset will be saved to the configured presets directory (either your custom path or the default Maya user path).


---

#### Loading an Existing Preset:

1.  Activate the Maya viewport where you want to apply the settings (by clicking in it).
2.  In the viewportCapture UI, you should see a list displaying available presets.
3.  Select the preset you wish to load from this list.
4.  Click the **"Load Selected"** button (or double-click with the left mouse button).
5.  The settings from the chosen preset will be applied to your active Maya viewport.


---
### Configuring Preset Paths (Optional)

You can customize where viewportCapture saves and loads its presets. This is especially useful for sharing presets across a team using a network drive.

#### Custom Preset Path

To change the primary path where presets are saved and loaded:

a.  Open the `viewportCapture_2025_v03.py` script file in a text editor.
b.  Find the line (around line 64, but may vary slightly with script versions) where `self.custom_preset_path` is defined. It will look similar to this:
    ```python
    self.custom_preset_path = "M:/MyProjectData/MayaViewportPresets/"
    ```
c.  Modify the path in the quotes to your desired directory. For example:
    ```python
    self.custom_preset_path = "P:/MyCustomData/MyMayaViewportPresets/"
    ```
d.  Save the changes to the `.py` script file.
e.  **Important:** Ensure the directory you specified exists and that Maya has the necessary read/write permissions for it. If the path is invalid, the directory doesn't exist, or permissions are insufficient, the script will revert to using the default preset path (see below).

#### Default Preset Path (Fallback)

If the 'Custom Preset Path' in the script is set to an empty string (e.g., `self.custom_preset_path = ""`), or if the specified custom directory does not exist or is inaccessible, the script will automatically use a default location within your Maya user application directory. This path is typically:

`[Your Maya User App Directory]/viewportCapture/presets/`

Common examples of the full default path:

-   **Windows:** `C:/Users/[YourUsername]/Documents/maya/viewportCapture/presets/`
-   **macOS:** `~/Library/Preferences/Autodesk/maya/viewportCapture/presets/`
-   **Linux:** `~/maya/viewportCapture/presets/`

The script will attempt to create this `viewportCapture/presets/` subdirectory if it's not already present when using the default path.

## Notes & Troubleshooting

-   The script is compatible with Maya 2022 and newer. For older Maya versions, adjustments might be necessary.
-   The 'gpuCache' plugin must be available and loadable in Maya for the GPU Cache feature to work.
-   If using a custom preset path, ensure the directory exists and Maya has write permissions.
-   The script is designed for Maya's Viewport 2.0.

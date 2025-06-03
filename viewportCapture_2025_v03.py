# viewportCapture 2025 v3
# Copyright (c) 2024 Giuseppe Pagnozzi
#
# This script is provided freely and generously.
# You can use, study, modify, and share it.
# It's licensed under the MIT License
# Visit https://opensource.org/licenses/MIT for the full terms.
"""
--------------------------------------------------------------------------------
Tool Info
--------------------------------------------------------------------------------
This tool allows users to capture the current display settings of an active Maya viewport, save them as presets, 
and apply these presets to other viewports or at a later time. A key feature is the generation of equivalent MEL scripts,
allowing users to easily re-apply these settings via custom shelves, shortcuts or scripts.
It primarily focuses on Viewport 2.0 settings.

Viewport Capture Tool Info
 Settings:
 - Custom Preset Path:
   - You can change the primary path where presets are saved and loaded.
   - To do this, modify the following line 52 in the script:
     `self.custom_preset_path = "M:/MyProjectData/MayaViewportPresets/"`
   - Replace `"M:/MyProjectData/MayaViewportPresets/"` with your desired directory path.
   - Ensure the directory exists, or the script will use the default Maya preset location.
 - Default Preset Path (Fallback):
   - If the 'Custom Preset Path' (above) is left empty, or if the specified custom directory does not exist,
     the script will automatically save and load presets from a default location within your Maya user application directory.
   - This default path is: `[Your Maya User App Directory]/viewportCapture/presets/`
   - (e.g., `C:/Users/[YourUsername]/Documents/maya/viewportCapture/presets/` on Windows,
     or `~/Library/Preferences/Autodesk/maya/viewportCapture/presets/` on macOS,
     or `~/maya/viewportCapture/presets/` on Linux).
   - The script will attempt to create this 'viewportCapture/presets/' subdirectory if it's not already present.
 - GPU Cache:
   - The "Enable GPU Cache" checkbox in the UI controls whether GPU caching is active in the selected viewport.
   - This requires the 'gpuCache' plugin to be loaded in Maya. The script will attempt to load it automatically if needed.
"""

import maya.cmds as cmds
import maya.mel as mel
import json
import os

class ViewportCapture:
    def __init__(self):
        self.window_name = "viewportCaptureWin"
        self.result_field = None
        self.status_label = None
        self.preset_list = None
        self.last_captured_settings = None
        self.gpu_cache_enabled = False  # Flag for GPU cache state. Change to True if you want GPU cache to be enabled by default at script startup.
        self.gpu_checkbox = None
        self.custom_preset_path = "M:/MyProjectData/MayaViewportPresets/"  # Add custom preset path variable here

        # Standard display attributes
        self.display_attrs = [
            'nurbsCurves', 'nurbsSurfaces', 'polymeshes', 'subdivSurfaces',
            'planes', 'lights', 'joints', 'ikHandles', 'deformers',
            'dynamics', 'fluids', 'hairSystems', 'follicles', 'nCloths',
            'nParticles', 'nRigids', 'dynamicConstraints', 'locators',
            'manipulators', 'grid', 'handles', 'pivots', 'textures',
            'strokes', 'selectionHiliteDisplay', 'headsUpDisplay',
            'displayLights', 'wireframeOnShaded', 'wireframe', 'xray',
            'backfaceCulling', 'smoothWireframe', 'displayTextures',
            'displayAppearance', 'useDefaultMaterial', 'hwFog', 'fogging',
            'dimensions', 'cv', 'particleInstancers', 'motionTrails',
            'cameras', 'imagePlane', 'hulls', 'twoSidedLighting', 'shadows', 
            'jointXray','activeComponentsXray'
        ]

        # Hardware 2.0 specific attributes
        self.hw2_attrs = {
            'multiSampleEnable': bool,
            'multiSampleCount': int,
            'ssaoEnable': bool,
            'ssaoAmount': float,
            'ssaoRadius': float,
            'ssaoFilterRadius': float,
            'motionBlurEnable': bool,
            'motionBlurSampleCount': int,
            'motionBlurShutterOpenFraction': float,
            'motionBlurShutterCloseFraction': float,
            'transparencyAlgorithm': int,
            'transparencyQuality': float,
            'transparencyShadowDepth': int,
            'lineAAEnable': bool,
            'maxHardwareLines': int,
            'minimumPixelWidth': float,
            'hwFogEnable': bool,
            'hwFogMode': int,
            'hwFogStart': float,
            'hwFogEnd': float,
            'hwFogDensity': float,
            'hwFogColor': 'float3',
            'hwFogFalloff': int,
            'hwFogRatio': float,
            'defaultLightIntensity': float,
            'consolidateWorld': bool,
            'maxHardwareLights': int,
            'transparentShadow': bool,
            'alphaCutPrepass': bool
        }

        self.create_main_ui()
        self.refresh_preset_list()

    def ensure_gpu_plugin_loaded(self):
        """Ensure GPU Cache plugin is loaded."""
        try:
            if not cmds.pluginInfo('gpuCache', query=True, loaded=True):
                cmds.loadPlugin('gpuCache')
                self.update_status("Loaded GPU Cache plugin")
                return True
        except Exception as e:
            self.update_status("Warning: Could not load GPU Cache plugin: {}".format(str(e)))
            return False
        return True

    def update_status(self, message):
        """Update the UI status label."""
        if self.status_label:
            cmds.text(self.status_label, edit=True, label="Status: " + message)

    def get_active_viewport(self):
        """Return a valid modelPanel currently in focus, or None if not found."""
        panel = cmds.getPanel(withFocus=True)
        if panel and cmds.getPanel(typeOf=panel) == 'modelPanel':
            return panel
        for p in cmds.getPanel(type='modelPanel'):
            if cmds.modelEditor(p, q=True, visible=True):
                return p
        return None

    def get_active_camera(self, panel):
        """Return the active camera for the given modelPanel."""
        camera = cmds.modelEditor(panel, q=True, camera=True)
        return camera

    def ensure_viewport_20(self, panel):
        """Ensure the given panel is set to Viewport 2.0."""
        current_renderer = cmds.modelEditor(panel, q=True, rendererName=True)
        try:
            if current_renderer != "vp2Renderer":
                cmds.modelEditor(panel, e=True, rendererName="vp2Renderer")
        except:
            self.update_status("Warning: Could not set Viewport 2.0 renderer")
        cmds.refresh()

    def capture_viewport(self, *args):
        """Capture the current viewport settings and display them."""
        panel = self.get_active_viewport()
        if not panel:
            self.update_status("No active viewport found")
            return

        self.ensure_viewport_20(panel)

        settings = self.capture_settings(panel)
        if settings:
            self.last_captured_settings = settings
            mel_code = self.settings_to_mel(settings)
            cmds.scrollField(self.result_field, edit=True, text=mel_code)
            self.update_status("Settings captured from {}".format(panel))
        else:
            self.update_status("Failed to capture settings")

    def capture_settings(self, panel):
        """Capture all viewport settings from the given panel."""
        if not panel:
            return None

        settings = {
            'panel': panel,
            'display': {},
            'background': {},
            'hardware2': {},
            'plugin_display': {'gpuCache': self.gpu_cache_enabled},
            'camera_gate': {},
            'camera_mask': {},
            'camera_filmfit': {}
        }

        active_camera = self.get_active_camera(panel)
        if active_camera:
            try:
                settings['camera_gate']['displayFilmGate'] = cmds.camera(active_camera, query=True, displayFilmGate=True)
                settings['camera_gate']['displayResolution'] = cmds.camera(active_camera, query=True, displayResolution=True)
                settings['camera_gate']['overscan'] = cmds.camera(active_camera, query=True, overscan=True)
            except Exception as e:
                self.update_status("Warning: Could not capture camera gate settings: {}".format(str(e)))

            try:
                settings['camera_mask']['displayGateMask'] = cmds.camera(active_camera, query=True, displayGateMask=True)
            except Exception as e:
                self.update_status("Warning: Could not capture camera gate mask setting: {}".format(str(e)))

            try:
                settings['camera_filmfit']['filmFit'] = cmds.camera(active_camera, query=True, filmFit=True)
            except Exception as e:
                self.update_status("Warning: Could not capture camera film fit setting: {}".format(str(e)))

        # Capture standard display attributes
        for attr in self.display_attrs:
            try:
                if attr == 'displayAppearance':
                    val = cmds.modelEditor(panel, q=True, displayAppearance=True)
                elif attr == 'hwFog':
                    val = cmds.modelEditor(panel, q=True, hwFog=True)
                    settings['display'][attr] = val
                    if not cmds.objExists('hardwareRenderingGlobals'):
                        cmds.createNode('hardwareRenderingGlobals')
                    cmds.setAttr('hardwareRenderingGlobals.hwFogEnable', val)
                elif attr == 'fogging':
                    val = cmds.modelEditor(panel, q=True, fogging=True)
                elif attr == 'shadows':
                    val = cmds.modelEditor(panel, q=True, shadows=True)
                elif attr == 'jointXray':
                    val = cmds.modelEditor(panel, q=True, jointXray=True)
                elif attr == 'activeComponentsXray':
                    val = cmds.modelEditor(panel, q=True, activeComponentsXray=True)
                else:
                    val = cmds.modelEditor(panel, q=True, **{attr: True})
                settings['display'][attr] = val
            except Exception as e:
                self.update_status("Warning: Could not capture {}: {}".format(attr, str(e)))

        # Capture background settings
        try:
            settings['background']['gradient'] = cmds.displayPref(query=True, displayGradient=True)
            settings['background']['color'] = cmds.displayRGBColor('background', q=True)
            settings['background']['topColor'] = cmds.displayRGBColor('backgroundTop', q=True)
            settings['background']['bottomColor'] = cmds.displayRGBColor('backgroundBottom', q=True)
        except Exception as e:
            self.update_status("Warning: Could not capture background settings: {}".format(str(e)))

        # Capture Hardware 2.0 settings
        if not cmds.objExists('hardwareRenderingGlobals'):
            cmds.createNode('hardwareRenderingGlobals')

        for attr, attr_type in self.hw2_attrs.items():
            try:
                if attr_type == 'float3':
                    val = cmds.getAttr('hardwareRenderingGlobals.' + attr)[0]
                else:
                    val = cmds.getAttr('hardwareRenderingGlobals.' + attr)
                settings['hardware2'][attr] = val
            except Exception as e:
                self.update_status("Warning: Could not capture HW2 setting {}: {}".format(attr, str(e)))

        return settings

    def apply_settings(self, *args):
        """Apply the last captured settings to the active viewport."""
        if not self.last_captured_settings:
            self.update_status("No settings to apply")
            return

        panel = self.get_active_viewport()
        if not panel:
            self.update_status("No active viewport found")
            return

        self.ensure_viewport_20(panel)

        try:
            cmds.undoInfo(openChunk=True)

            # Apply camera gate settings
            camera_gate_settings = self.last_captured_settings.get('camera_gate', {})
            active_camera = self.get_active_camera(panel)
            if active_camera and camera_gate_settings:
                try:
                    if 'displayFilmGate' in camera_gate_settings:
                        cmds.camera(active_camera, edit=True, displayFilmGate=camera_gate_settings['displayFilmGate'])
                    if 'displayResolution' in camera_gate_settings:
                        cmds.camera(active_camera, edit=True, displayResolution=camera_gate_settings['displayResolution'])
                    if 'overscan' in camera_gate_settings:
                        cmds.camera(active_camera, edit=True, overscan=camera_gate_settings['overscan'])
                except Exception as e:
                    self.update_status("Warning: Could not apply camera gate settings: {}".format(str(e)))

            # Apply camera mask settings
            camera_mask_settings = self.last_captured_settings.get('camera_mask', {})
            if active_camera and camera_mask_settings:
                try:
                    if 'displayGateMask' in camera_mask_settings:
                        cmds.camera(active_camera, edit=True, displayGateMask=camera_mask_settings['displayGateMask'])
                except Exception as e:
                    self.update_status("Warning: Could not apply camera gate mask setting: {}".format(str(e)))

            # Apply camera film fit settings
            camera_filmfit_settings = self.last_captured_settings.get('camera_filmfit', {})
            if active_camera and camera_filmfit_settings:
                try:
                    if 'filmFit' in camera_filmfit_settings:
                        cmds.camera(active_camera, edit=True, filmFit=camera_filmfit_settings['filmFit'])
                except Exception as e:
                    self.update_status("Warning: Could not apply camera film fit setting: {}".format(str(e)))

            # Apply standard display settings
            for attr, value in self.last_captured_settings['display'].items():
                try:
                    if attr == 'displayAppearance':
                        cmds.modelEditor(panel, e=True, displayAppearance=value)
                    elif attr == 'hwFog':
                        cmds.modelEditor(panel, e=True, hwFog=value)
                        if not cmds.objExists('hardwareRenderingGlobals'):
                            cmds.createNode('hardwareRenderingGlobals')
                        cmds.setAttr('hardwareRenderingGlobals.hwFogEnable', value)
                    elif attr == 'fogging':
                        cmds.modelEditor(panel, e=True, fogging=value)
                    elif attr == 'shadows':
                         cmds.modelEditor(panel, e=True, shadows=value)
                    elif attr == 'jointXray':
                        cmds.modelEditor(panel, e=True, jointXray=value)
                    elif attr == 'activeComponentsXray':
                        cmds.modelEditor(panel, e=True, activeComponentsXray=value)
                    else:
                        cmds.modelEditor(panel, e=True, **{attr: value})
                except Exception as e:
                     self.update_status("Warning: Could not apply {}: {}".format(attr, str(e)))

            # Apply GPU Cache settings
            if 'plugin_display' in self.last_captured_settings:
                gpu_state = self.last_captured_settings['plugin_display']['gpuCache']
                if gpu_state and self.ensure_gpu_plugin_loaded():
                    cmds.modelEditor(panel, edit=True, pluginObjects=('gpuCacheDisplayFilter', True))
                else:
                    cmds.modelEditor(panel, edit=True, pluginObjects=('gpuCacheDisplayFilter', False))
                self.gpu_cache_enabled = gpu_state
                cmds.checkBox(self.gpu_checkbox, edit=True, value=self.gpu_cache_enabled)

            # Apply background settings
            bg = self.last_captured_settings.get('background', {})
            try:
                if 'gradient' in bg:
                    cmds.displayPref(displayGradient=bg['gradient'])
                if 'topColor' in bg:
                    cmds.displayRGBColor('backgroundTop', *bg['topColor'])
                if 'color' in bg:
                    cmds.displayRGBColor('background', *bg['color'])
                if bg.get('gradient') and 'bottomColor' in bg:
                    cmds.displayRGBColor('backgroundBottom', *bg['bottomColor'])
            except Exception as e:
                self.update_status("Warning: Could not apply background settings: {}".format(str(e)))

            # Apply Hardware 2.0 settings
            hw2_settings = self.last_captured_settings.get('hardware2', {})
            if hw2_settings:
                if not cmds.objExists('hardwareRenderingGlobals'):
                    cmds.createNode('hardwareRenderingGlobals')

                for attr, value in hw2_settings.items():
                    try:
                        if isinstance(value, (list, tuple)):
                            cmds.setAttr('hardwareRenderingGlobals.' + attr, *value, type='double3')
                        else:
                            cmds.setAttr('hardwareRenderingGlobals.' + attr, value)
                    except Exception as e:
                        self.update_status("Warning: Could not apply HW2 setting {}: {}".format(attr, str(e)))

            self.update_status("Settings applied successfully")

        except Exception as e:
            self.update_status("Error applying settings: {}".format(str(e)))
        finally:
            cmds.undoInfo(closeChunk=True)

    def settings_to_mel(self, settings):
        """Convert settings to MEL script."""
        if not settings:
            return "// No settings captured"

        mel_commands = [
            '// Viewport Settings - Generated by viewportCapture',
            'global proc viewportCaptureApply()',
            '{',
            '    string $panel = `getPanel -withFocus`;',
            '    if (`getPanel -typeOf $panel` != "modelPanel")',
            '    {',
            '        string $modelPanels[] = `getPanel -type "modelPanel"`;',
            '        $panel = "";',
            '        if (size($modelPanels) > 0)',
            '        {',
            '            $panel = $modelPanels[0];',
            '        }',
            '        if ($panel == "")',
            '        {',
            '            error "No valid modelPanel found.\\nPlease open a viewport first.";',
            '            return;',
            '        }',
            '    }',
            '',
            '    // Set Viewport 2.0 renderer',
            '    modelEditor -e -rendererName "vp2Renderer" $panel;',
            '',
            '    string $camera = `modelEditor -q -camera $panel`;',
            '    if ($camera != "")',
            '    {',
            '        // Camera Gate Settings'
        ]

        # Add Camera Gate settings
        if 'camera_gate' in settings:
            camera_gate = settings['camera_gate']
            if 'displayFilmGate' in camera_gate:
                mel_commands.append('        camera -e -displayFilmGate {} $camera;'.format(str(camera_gate["displayFilmGate"]).lower()))
            if 'displayResolution' in camera_gate:
                mel_commands.append('        camera -e -displayResolution {} $camera;'.format(str(camera_gate["displayResolution"]).lower()))
            if 'overscan' in camera_gate:
                mel_commands.append('        camera -e -overscan {} $camera;'.format(camera_gate["overscan"]))

        # Add Camera Mask settings
        if 'camera_mask' in settings:
            camera_mask = settings['camera_mask']
            if 'displayGateMask' in camera_mask:
                mel_commands.append('        camera -e -displayGateMask {} $camera;'.format(str(camera_mask["displayGateMask"]).lower()))

        # Add Camera Film Fit settings
        if 'camera_filmfit' in settings:
            camera_filmfit = settings['camera_filmfit']
            if 'filmFit' in camera_filmfit:
                mel_commands.append('        camera -e -filmFit {} $camera;'.format(camera_filmfit["filmFit"]))

        mel_commands.append('    }')
        mel_commands.append('')

        # Add GPU Cache settings
        mel_commands.extend([
            '    // GPU Cache Settings',
            '    if (!`pluginInfo -q -loaded "gpuCache"`)',
            '    {',
            '        loadPlugin "gpuCache";',
            '    }',
            '    modelEditor -e -pluginObjects gpuCacheDisplayFilter {} $panel;'.format(str(settings.get("plugin_display", {}).get("gpuCache", False)).lower()),
            ''
        ])

        # Add display settings
        mel_commands.append('    // Display Settings')
        for attr, value in settings['display'].items():
            if attr == 'hwFog':
                mel_commands.append('    modelEditor -e -hwFog {} $panel;'.format(str(value).lower()))
                mel_commands.append('    if (!`objExists "hardwareRenderingGlobals"`) {')
                mel_commands.append('        createNode "hardwareRenderingGlobals";')
                mel_commands.append('    }')
                mel_commands.append('    setAttr "hardwareRenderingGlobals.hwFogEnable" {};'.format(int(value)))
            elif attr == 'fogging':
                mel_commands.append('    modelEditor -e -fogging {} $panel;'.format(str(value).lower()))
            elif attr in ['displayLights', 'displayAppearance']:
                mel_commands.append('    modelEditor -e -{0} "{1}" $panel;'.format(attr, value))
            elif attr == 'twoSidedLighting':
                 mel_commands.append('    modelEditor -e -twoSidedLighting {} $panel;'.format(str(value).lower()))
            elif attr == 'shadows':
                mel_commands.append('    modelEditor -e -shadows {} $panel;'.format(str(value).lower()))
            elif attr == 'jointXray':
                mel_commands.append('    modelEditor -e -jointXray {} $panel;'.format(str(value).lower()))
            elif attr == 'activeComponentsXray':
                mel_commands.append('    modelEditor -e -activeComponentsXray {} $panel;'.format(str(value).lower()))
            else:
                mel_commands.append('    modelEditor -e -{0} {1} $panel;'.format(attr, str(value).lower()))

        # Add background settings
        if 'background' in settings:
            mel_commands.append('')
            mel_commands.append('    // Background Settings')
            bg = settings['background']
            if 'gradient' in bg:
                mel_commands.append('    displayPref -displayGradient {};'.format(str(bg["gradient"]).lower()))
            if 'topColor' in bg:
                top_color = bg['topColor']
                mel_commands.append('    displayRGBColor "backgroundTop" {0} {1} {2};'.format(
                    top_color[0], top_color[1], top_color[2]))
            if 'color' in bg:
                color = bg['color']
                mel_commands.append('    displayRGBColor "background" {0} {1} {2};'.format(
                    color[0], color[1], color[2]))
            if bg.get('gradient') and 'bottomColor' in bg:
                bottom_color = bg['bottomColor']
                mel_commands.append('    displayRGBColor "backgroundBottom" {0} {1} {2};'.format(
                    bottom_color[0], bottom_color[1], bottom_color[2]))

        # Add Hardware 2.0 settings
        if 'hardware2' in settings:
            mel_commands.append('')
            mel_commands.append('    // Hardware 2.0 Settings')
            mel_commands.append('    if (!`objExists "hardwareRenderingGlobals"`) {')
            mel_commands.append('        createNode "hardwareRenderingGlobals";')
            mel_commands.append('    }')

            for attr, value in settings['hardware2'].items():
                if isinstance(value, bool):
                    value = int(value)
                if isinstance(value, (list, tuple)):
                    mel_commands.append('    setAttr "hardwareRenderingGlobals.{0}" -type double3 {1} {2} {3};'.format(
                        attr, value[0], value[1], value[2]))
                else:
                    mel_commands.append('    setAttr "hardwareRenderingGlobals.{0}" {1};'.format(attr, value))

        mel_commands.extend(['}', '', 'viewportCaptureApply();'])
        return '\n'.join(mel_commands)

    def get_preset_dir(self):
        """Ensure and return the presets directory, prioritizing custom path."""
        if self.custom_preset_path and os.path.isdir(self.custom_preset_path):
            return self.custom_preset_path
        else:
            maya_app_dir = cmds.internalVar(userAppDir=True)
            preset_dir = os.path.join(maya_app_dir, 'viewportCapture', 'presets')
            if not os.path.exists(preset_dir):
                os.makedirs(preset_dir)
            return preset_dir

    def toggle_gpu_cache(self, *args):
        """Toggle GPU Cache state based on checkbox."""
        self.gpu_cache_enabled = cmds.checkBox(self.gpu_checkbox, query=True, value=True)
        if self.gpu_cache_enabled:
            if self.ensure_gpu_plugin_loaded():
                self.update_status("GPU Cache enabled")
            else:
                self.gpu_cache_enabled = False
                cmds.checkBox(self.gpu_checkbox, edit=True, value=False)
                self.update_status("Failed to enable GPU Cache - plugin could not be loaded")
        else:
            self.update_status("GPU Cache disabled")

    def save_preset(self, *args):
        """Save the current settings as a preset, with overwrite confirmation."""
        if not self.last_captured_settings:
            self.update_status("No settings to save")
            return

        result = cmds.promptDialog(
            title='Save Preset',
            message='Enter preset name:',
            button=['Save', 'Cancel'],
            defaultButton='Save',
            cancelButton='Cancel',
            dismissString='Cancel'
        )

        if result == 'Save':
            name = cmds.promptDialog(query=True, text=True)
            if name:
                preset_path = os.path.join(self.get_preset_dir(), name + ".json")

                if os.path.exists(preset_path):
                    confirm_result = cmds.confirmDialog(
                        title='Overwrite Preset?',
                        message='A preset with the name "{}" already exists. Overwrite?'.format(name),
                        button=['Yes', 'No'],
                        defaultButton='No',
                        cancelButton='No',
                        dismissString='No'
                    )
                    if confirm_result == 'No':
                        self.update_status("Save cancelled.")
                        return  

                try:
                    with open(preset_path, 'w') as f:
                        json.dump(self.last_captured_settings, f, indent=4)
                    self.update_status("Preset '{}' saved".format(name))
                    self.refresh_preset_list()
                except Exception as e:
                    self.update_status("Error saving preset: {}".format(e))


    def load_preset(self, *args):
        """Load and apply the selected preset (via MEL)."""
        selected = cmds.textScrollList(self.preset_list, q=True, selectItem=True)
        if not selected:
            self.update_status("No preset selected")
            return

        preset_path = os.path.join(self.get_preset_dir(), selected[0] + ".json")
        try:
            with open(preset_path, 'r') as f:
                settings = json.load(f)
                self.last_captured_settings = settings
                self.gpu_cache_enabled = settings.get('plugin_display', {}).get('gpuCache', False)
                cmds.checkBox(self.gpu_checkbox, edit=True, value=self.gpu_cache_enabled)

                # Generate the MEL script from these settings:
                mel_code = self.settings_to_mel(settings)

                # Display the MEL code in the scrollField
                cmds.scrollField(self.result_field, edit=True, text=mel_code)

                # Execute the MEL code in Maya
                mel.eval(mel_code)

                # If you DO NOT want Python to apply anything, comment out the line below:
                # self.apply_settings()

                self.update_status("Preset '{}' loaded and applied".format(selected[0]))
        except Exception as e:
            self.update_status("Error loading preset: {}".format(e))

    def delete_preset(self, *args):
        """Delete the selected preset."""
        selected = cmds.textScrollList(self.preset_list, q=True, selectItem=True)
        if not selected:
            self.update_status("No preset selected")
            return

        result = cmds.confirmDialog(
            title='Delete Preset',
            message='Delete preset "{}"?'.format(selected[0]),
            button=['Yes', 'No'],
            defaultButton='No',
            cancelButton='No',
            dismissString='No'
        )

        if result == 'Yes':
            preset_path = os.path.join(self.get_preset_dir(), selected[0] + ".json")
            try:
                os.remove(preset_path)
                self.update_status("Preset '{}' deleted".format(selected[0]))
                self.refresh_preset_list()
            except Exception as e:
                self.update_status("Error deleting preset: {}".format(e))

    def refresh_preset_list(self):
        """Refresh the preset list in the UI."""
        cmds.textScrollList(self.preset_list, edit=True, removeAll=True)
        preset_dir = self.get_preset_dir()
        if os.path.exists(preset_dir):
            presets = [f[:-5] for f in os.listdir(preset_dir) if f.endswith('.json')]
            if presets:
                cmds.textScrollList(self.preset_list, edit=True, append=sorted(presets))

    def create_main_ui(self):
        """Create the main user interface."""
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)

        cmds.window(self.window_name, title="Viewport Capture 2025 v3", widthHeight=(600, 800))

        # Main layout
        main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5)

        cmds.text(label="Viewport Capture 2025 v3", font="boldLabelFont", height=30)
        cmds.separator(height=10, style='double')

        btn_layout = cmds.rowLayout(numberOfColumns=2, columnWidth2=(290, 290),
                                    columnAttach=[(1, 'both', 5), (2, 'both', 5)])
        cmds.button(label="Capture Active Viewport", command=self.capture_viewport)
        cmds.button(label="Apply Settings", command=self.apply_settings)
        cmds.setParent(main_layout)

        # Options
        options_layout = cmds.columnLayout(adjustableColumn=True)
        cmds.setParent(options_layout)
        # GPU Cache checkbox
        self.gpu_checkbox = cmds.checkBox(
            label="Enable GPU Cache",
            value=self.gpu_cache_enabled,
            changeCommand=self.toggle_gpu_cache,
            align="left"
        )
        cmds.setParent(main_layout)

        self.status_label = cmds.text(label="Status: Ready", align='left')
        cmds.separator(height=10)

        cmds.text(label="Captured Settings:", align='left')
        self.result_field = cmds.scrollField(wordWrap=False, height=300,
                                             text="// Capture a viewport to see settings")

        cmds.separator(height=20)
        cmds.text(label="Presets:", align='left')

        self.preset_list = cmds.textScrollList(height=150,
                                               allowMultiSelection=False,
                                               doubleClickCommand=self.load_preset)

        preset_btn_layout = cmds.rowLayout(numberOfColumns=3,
                                           columnWidth3=(190, 190, 190),
                                           columnAttach=[(1, 'both', 5),
                                                         (2, 'both', 5),
                                                         (3, 'both', 5)])
        cmds.button(label="Save New Preset", command=self.save_preset)
        cmds.button(label="Load Selected", command=self.load_preset)
        cmds.button(label="Delete Selected", command=self.delete_preset)
        cmds.setParent(main_layout)

        cmds.showWindow(self.window_name)

if __name__ == "__main__":
    ViewportCapture()
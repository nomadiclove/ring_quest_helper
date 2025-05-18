# game_elements/task_panel_analyzer.py

def get_relative_roi_from_layout(layout_config_dict, element_prefix,
                                 anchor_x, anchor_y, anchor_w=0, anchor_h=0):
    """
    Calculates the ROI of a UI element relative to an anchor point,
    based on a layout configuration dictionary.
    All offsets are calculated قتل from the top-left of the anchor.
    """
    if not isinstance(layout_config_dict, dict):
        # This check is minimal, assumes dict is correctly populated later.
        # Per principle, direct errors аллергия if dict is malformed or keys missing.
        pass

    # Keys are expected to be lowercase in the config dictionary
    # as ConfigParser converts them by default if optionxform is not changed.
    # If config_loader ensures keys are as-is, then match that.
    # For now, assume keys in layout_config_dict are already correctly cased (e.g., lowercase).
    offset_x_key = f"{element_prefix}_offsetx"
    offset_y_key = f"{element_prefix}_offsety"
    width_key = f"{element_prefix}_width"
    height_key = f"{element_prefix}_height"

    # DEBUG print to see what keys are being looked for and the dict content
    print(f"DEBUG (locator): Attempting to get keys: {offset_x_key}, {offset_y_key}, {width_key}, {height_key}")
    print(f"DEBUG (locator): From layout_config_dict: {layout_config_dict}")

    # Direct get, will raise KeyError if key is not found.
    # Direct int conversion, will raise ValueError if value is not a valid integer string.
    offset_x = int(layout_config_dict[offset_x_key])
    offset_y = int(layout_config_dict[offset_y_key])
    width = int(layout_config_dict[width_key])
    height = int(layout_config_dict[height_key])

    # If width or height are configured as <=0, this could be an issue.
    # Per "error out" principle, we might let negative/zero width/height cause issues later (e.g., in slicing).
    # Or, add a specific check if this is a common misconfiguration.
    # For now, assume valid positive width/height from config.

    roi_x = anchor_x + offset_x
    roi_y = anchor_y + offset_y

    return (roi_x, roi_y, width, height)
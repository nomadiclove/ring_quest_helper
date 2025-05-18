# import configparser # 这个模块不直接读取配置文件，而是接收配置字典

def get_relative_roi_from_layout(layout_config_dict, element_prefix, 
                                 anchor_x, anchor_y, anchor_w=0, anchor_h=0):
    """
    根据UI布局配置字典和锚点坐标/尺寸，计算指定UI元素的相对ROI。
    所有偏移量都是相对于锚点左上角 (anchor_x, anchor_y) 计算的。
    如果配置文件中包含 _From_AnchorBottom 或 _From_AnchorRight 类型的偏移，
    则需要 anchor_w 和 anchor_h。

    参数:
    - layout_config_dict (dict): 从配置文件加载的包含UI布局信息的字典 
                                 (例如，'TaskTrackerUI_Layout' 段落的内容)。
    - element_prefix (str): UI元素在配置项中的前缀 (例如 'TaskType', 'TaskDesc')。
    - anchor_x (int): 锚点在父图像中的X坐标 (通常是 "任务追踪" 模板的左上角x)。
    - anchor_y (int): 锚点在父图像中的Y坐标 (通常是 "任务追踪" 模板的左上角y)。
    - anchor_w (int, optional): 锚点的宽度 (例如 "任务追踪" 模板的宽度)。
                                用于计算相对于锚点右边或底边的偏移。
    - anchor_h (int, optional): 锚点的高度 (例如 "任务追踪" 模板的高度)。
                                用于计算相对于锚点右边或底边的偏移。

    返回:
    - tuple: (roi_x, roi_y, roi_w, roi_h) UI元素相对于父图像的ROI。
    - None: 如果配置项缺失或类型错误。
    """
    if not layout_config_dict or not isinstance(layout_config_dict, dict):
        return None

    try:
        # 键名约定： {element_prefix}_OffsetX, {element_prefix}_OffsetY, 
        #            {element_prefix}_Width, {element_prefix}_Height
        # OffsetX/Y 是相对于 anchor_x, anchor_y 的
        # 例如：TaskType_OffsetX, TaskType_OffsetY, TaskType_Width, TaskType_Height

        offset_x_key = f"{element_prefix}_OffsetX".lower() # ConfigParser键名不区分大小写，但python字典区分
        offset_y_key = f"{element_prefix}_OffsetY".lower()
        width_key = f"{element_prefix}_Width".lower()
        height_key = f"{element_prefix}_Height".lower()

        # 从字典中获取值，并转换为整数
        # 我们假设 config_loader 已经将值作为字符串存入字典，或者这里直接用 getint
        # 为了简单，这里假设字典中的值已经是字符串形式的数字
        offset_x = int(layout_config_dict.get(offset_x_key, "0"))
        offset_y = int(layout_config_dict.get(offset_y_key, "0"))
        width = int(layout_config_dict.get(width_key, "0"))
        height = int(layout_config_dict.get(height_key, "0"))

        if width <= 0 or height <= 0:
            # print(f"警告 (get_relative_roi): 元素 '{element_prefix}' 的宽度或高度配置无效 ({width}x{height})。") # 暂时不打印
            return None 

        # --- 核心计算逻辑 ---
        # 默认偏移是相对于锚点的左上角 (anchor_x, anchor_y)
        # 如果你的配置文件中定义的 OffsetY 是想相对于锚点的底部 (header_rel_y + header_h)
        # 那么在调用此函数前，你需要将 anchor_y 调整为 header_rel_y + header_h
        # 或者，我们可以在这里增加对不同偏移基准的判断，但这会增加函数的复杂度。
        # 当前函数假设传入的 anchor_x, anchor_y 就是计算所有偏移的直接基准点。

        # 根据我们之前讨论的，你的配置是直接相对于 header_rel_x, header_rel_y 的绝对偏移量
        # 例如：TaskType_OffsetX = (期望的TaskType的X坐标) - header_rel_x
        #       TaskType_OffsetY = (期望的TaskType的Y坐标) - header_rel_y
        # 所以，这里的计算是：
        roi_x = anchor_x + offset_x
        roi_y = anchor_y + offset_y

        return (roi_x, roi_y, width, height)

    except (KeyError, ValueError, TypeError): # 捕获字典键不存在或值无法转为整数的错误
        # print(f"错误 (get_relative_roi): 处理元素 '{element_prefix}' 配置时出错 - {e}") # 暂时不打印
        # import traceback
        # traceback.print_exc() # 调试时可以打开
        return None
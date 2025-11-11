from PIL import Image, ImageDraw, ImageFont
import os

def merge_png_images_with_config(image_paths, output_path, config_info=None, direction='horizontal', spacing=0, output_format='PNG'):
    """
    合并多个PNG图片并添加配置信息标注
    
    参数:
    image_paths: 图片路径列表
    output_path: 输出图片路径
    config_info: 配置信息字典，如 {"模型": "ResNet50", "批次大小": 32}
    direction: 合并方向 ('horizontal' 水平, 'vertical' 垂直)
    spacing: 图片之间的间距（像素）
    output_format: 输出格式 ('PNG', 'JPEG', 'BMP', 'TIFF', 'GIF')
    """
    # 打开所有图片
    images = []
    for path in image_paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f"图片不存在: {path}")
        img = Image.open(path).convert("RGBA")
        images.append(img)
    
    if not images:
        raise ValueError("没有有效的图片需要合并")
    
    # 支持的输出格式
    supported_formats = {
        'PNG': 'PNG',
        'JPEG': 'JPEG', 
        'JPG': 'JPEG',
        'BMP': 'BMP',
        'TIFF': 'TIFF',
        'TIF': 'TIFF',
        'GIF': 'GIF'
    }
    
    output_format = output_format.upper()
    if output_format not in supported_formats:
        raise ValueError(f"不支持的输出格式: {output_format}. 支持的格式: {list(supported_formats.keys())}")
    
    # 配置信息区域的高度
    config_height = 0
    if config_info:
        config_height = 60  # 为配置信息预留空间
    
    if direction == 'horizontal':
        # 水平合并
        total_width = sum(img.width for img in images) + spacing * (len(images) - 1)
        max_height = max(img.height for img in images)
        final_height = max_height + config_height
        
        # 创建新画布
        if output_format in ['JPEG', 'BMP', 'TIFF']:
            merged_img = Image.new('RGB', (total_width, final_height), (255, 255, 255))
        else:
            merged_img = Image.new('RGBA', (total_width, final_height), (255, 255, 255, 0))
        
        # 添加配置信息
        if config_info:
            draw = ImageDraw.Draw(merged_img)
            
            # 尝试加载字体，如果失败则使用默认字体
            try:
                font = ImageFont.truetype("arial.ttf", 14)
            except:
                try:
                    font = ImageFont.truetype("DejaVuSans.ttf", 14)
                except:
                    font = ImageFont.load_default()
            
            # 绘制配置信息背景
            draw.rectangle([0, 0, total_width, config_height], fill=(240, 240, 240))
            
            # 绘制配置信息文本
            y_pos = 10
            for key, value in config_info.items():
                text = f"{key}: {value}"
                try:
                    draw.text((10, y_pos), text, fill=(0, 0, 0), font=font)
                except:
                    draw.text((10, y_pos), text, fill=(0, 0, 0))
                y_pos += 20
        
        # 粘贴图片
        x_offset = 0
        for img in images:
            if output_format in ['JPEG', 'BMP', 'TIFF']:
                # 如果是不支持透明度的格式，需要处理透明背景
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    # 创建白色背景
                    background = Image.new('RGBA', img.size, (255, 255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background.convert('RGB')
                
            y_offset = config_height + (final_height - config_height - img.height) // 2  # 垂直居中
            merged_img.paste(img, (x_offset, y_offset))
            x_offset += img.width + spacing
            
    elif direction == 'vertical':
        # 垂直合并
        max_width = max(img.width for img in images)
        total_height = sum(img.height for img in images) + spacing * (len(images) - 1)
        final_height = total_height + config_height
        
        # 创建新画布
        if output_format in ['JPEG', 'BMP', 'TIFF']:
            merged_img = Image.new('RGB', (max_width, final_height), (255, 255, 255))
        else:
            merged_img = Image.new('RGBA', (max_width, final_height), (255, 255, 255, 0))
        
        # 添加配置信息
        if config_info:
            draw = ImageDraw.Draw(merged_img)
            
            # 尝试加载字体
            try:
                font = ImageFont.truetype("arial.ttf", 14)
            except:
                try:
                    font = ImageFont.truetype("DejaVuSans.ttf", 14)
                except:
                    font = ImageFont.load_default()
            
            # 绘制配置信息背景
            draw.rectangle([0, 0, max_width, config_height], fill=(240, 240, 240))
            
            # 绘制配置信息文本
            y_pos = 10
            for key, value in config_info.items():
                text = f"{key}: {value}"
                try:
                    draw.text((10, y_pos), text, fill=(0, 0, 0), font=font)
                except:
                    draw.text((10, y_pos), text, fill=(0, 0, 0))
                y_pos += 20
        
        # 粘贴图片
        y_offset = config_height
        for img in images:
            if output_format in ['JPEG', 'BMP', 'TIFF']:
                # 如果是不支持透明度的格式，需要处理透明背景
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    # 创建白色背景
                    background = Image.new('RGBA', img.size, (255, 255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background.convert('RGB')
            
            x_offset = (max_width - img.width) // 2  # 水平居中
            merged_img.paste(img, (x_offset, y_offset))
            y_offset += img.height + spacing
    else:
        raise ValueError("direction 参数必须是 'horizontal' 或 'vertical'")
    
    # 保存合并后的图片
    save_kwargs = {}
    if output_format == 'JPEG':
        save_kwargs['quality'] = 95  # JPEG质量
        save_kwargs['optimize'] = True
    elif output_format == 'GIF':
        save_kwargs['save_all'] = True
        if merged_img.mode != 'P':
            merged_img = merged_img.convert('P', palette=Image.ADAPTIVE)
    
    merged_img.save(output_path, format=output_format, **save_kwargs)
    print(f"合并完成，输出图片: {output_path} (格式: {output_format})")

def merge_png_grid_with_config(image_paths, output_path, config_info=None, rows=None, cols=None, output_format='PNG'):
    """
    将图片按网格形式合并并添加配置信息标注
    
    参数:
    image_paths: 图片路径列表
    output_path: 输出图片路径
    config_info: 配置信息字典
    rows: 行数（如果未指定，会自动计算）
    cols: 列数（如果未指定，会自动计算）
    output_format: 输出格式 ('PNG', 'JPEG', 'BMP', 'TIFF', 'GIF')
    """
    # 打开所有图片
    images = []
    for path in image_paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f"图片不存在: {path}")
        img = Image.open(path).convert("RGBA")
        images.append(img)
    
    if not images:
        raise ValueError("没有有效的图片需要合并")
    
    # 支持的输出格式
    supported_formats = {
        'PNG': 'PNG',
        'JPEG': 'JPEG',
        'JPG': 'JPEG',
        'BMP': 'BMP',
        'TIFF': 'TIFF',
        'TIF': 'TIFF',
        'GIF': 'GIF'
    }
    
    output_format = output_format.upper()
    if output_format not in supported_formats:
        raise ValueError(f"不支持的输出格式: {output_format}. 支持的格式: {list(supported_formats.keys())}")
    
    # 计算网格布局
    total_images = len(images)
    if cols is None and rows is None:
        cols = int(total_images ** 0.5)  # 默认为近似正方形布局
        rows = (total_images + cols - 1) // cols
    elif rows is None:
        rows = (total_images + cols - 1) // cols
    elif cols is None:
        cols = (total_images + rows - 1) // rows
    
    # 计算最大尺寸以统一网格
    max_width = max(img.width for img in images)
    max_height = max(img.height for img in images)
    
    # 配置信息区域的高度
    config_height = 80 if config_info else 0
    
    # 创建网格画布
    grid_width = cols * max_width
    grid_height = rows * max_height
    final_height = grid_height + config_height
    
    if output_format in ['JPEG', 'BMP', 'TIFF']:
        grid_img = Image.new('RGB', (grid_width, final_height), (255, 255, 255))
    else:
        grid_img = Image.new('RGBA', (grid_width, final_height), (255, 255, 255, 0))
    
    # 添加配置信息
    if config_info:
        draw = ImageDraw.Draw(grid_img)
        
        # 尝试加载字体
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except:
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", 14)
            except:
                font = ImageFont.load_default()
        
        # 绘制配置信息背景
        draw.rectangle([0, 0, grid_width, config_height], fill=(240, 240, 240))
        
        # 绘制配置信息文本
        y_pos = 10
        for key, value in config_info.items():
            text = f"{key}: {value}"
            try:
                draw.text((10, y_pos), text, fill=(0, 0, 0), font=font)
            except:
                draw.text((10, y_pos), text, fill=(0, 0, 0))
            y_pos += 20
    
    # 粘贴图片到网格
    for idx, img in enumerate(images):
        row = idx // cols
        col = idx % cols
        x = col * max_width + (max_width - img.width) // 2
        y = config_height + row * max_height + (max_height - img.height) // 2  # 添加配置信息偏移
        
        # 处理透明度
        if output_format in ['JPEG', 'BMP', 'TIFF']:
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                # 创建白色背景
                background = Image.new('RGBA', img.size, (255, 255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background.convert('RGB')
        
        grid_img.paste(img, (x, y))
    
    # 保存合并后的图片
    save_kwargs = {}
    if output_format == 'JPEG':
        save_kwargs['quality'] = 95  # JPEG质量
        save_kwargs['optimize'] = True
    elif output_format == 'GIF':
        save_kwargs['save_all'] = True
        if grid_img.mode != 'P':
            grid_img = grid_img.convert('P', palette=Image.ADAPTIVE)
    
    grid_img.save(output_path, format=output_format, **save_kwargs)
    print(f"网格合并完成，输出图片: {output_path} (格式: {output_format})")

def merge_with_custom_config(image_paths, output_path, config_info=None, title=None, direction='horizontal', 
                            spacing=0, output_format='PNG', config_position='top'):
    """
    合并图片并添加自定义配置信息
    
    参数:
    image_paths: 图片路径列表
    output_path: 输出图片路径
    config_info: 配置信息字典
    title: 标题文字
    direction: 合并方向
    spacing: 图片间距
    output_format: 输出格式
    config_position: 配置信息位置 ('top', 'bottom', 'left', 'right')
    """
    # 打开所有图片
    images = []
    for path in image_paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f"图片不存在: {path}")
        img = Image.open(path).convert("RGBA")
        images.append(img)
    
    if not images:
        raise ValueError("没有有效的图片需要合并")
    
    # 支持的输出格式
    supported_formats = {
        'PNG': 'PNG',
        'JPEG': 'JPEG',
        'JPG': 'JPEG',
        'BMP': 'BMP',
        'TIFF': 'TIFF',
        'TIF': 'TIFF',
        'GIF': 'GIF'
    }
    
    output_format = output_format.upper()
    if output_format not in supported_formats:
        raise ValueError(f"不支持的输出格式: {output_format}. 支持的格式: {list(supported_formats.keys())}")
    
    # 配置信息区域的尺寸
    config_width = config_height = 0
    if config_info or title:
        if config_position in ['top', 'bottom']:
            config_height = 100
        else:  # left, right
            config_width = 200
    
    if direction == 'horizontal':
        total_width = sum(img.width for img in images) + spacing * (len(images) - 1)
        max_height = max(img.height for img in images)
        
        if config_position in ['top', 'bottom']:
            final_width = total_width
            final_height = max_height + config_height
            config_y = 0 if config_position == 'top' else max_height
        else:  # left, right
            final_width = total_width + config_width
            final_height = max(max_height, config_height)
            config_x = 0 if config_position == 'left' else total_width
    
    elif direction == 'vertical':
        max_width = max(img.width for img in images)
        total_height = sum(img.height for img in images) + spacing * (len(images) - 1)
        
        if config_position in ['top', 'bottom']:
            final_width = max(max_width, config_width)
            final_height = total_height + config_height
            config_y = 0 if config_position == 'top' else total_height
        else:  # left, right
            final_width = max_width + config_width
            final_height = total_height
            config_x = 0 if config_position == 'left' else max_width
    else:
        raise ValueError("direction 参数必须是 'horizontal' 或 'vertical'")
    
    # 创建新画布
    if output_format in ['JPEG', 'BMP', 'TIFF']:
        merged_img = Image.new('RGB', (final_width, final_height), (255, 255, 255))
    else:
        merged_img = Image.new('RGBA', (final_width, final_height), (255, 255, 255, 0))
    
    # 添加配置信息
    if config_info or title:
        draw = ImageDraw.Draw(merged_img)
        
        # 尝试加载字体
        try:
            font = ImageFont.truetype("arial.ttf", 16)
            small_font = ImageFont.truetype("arial.ttf", 12)
        except:
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", 16)
                small_font = ImageFont.truetype("DejaVuSans.ttf", 12)
            except:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
        
        # 绘制配置信息区域
        if config_position in ['top', 'bottom']:
            draw.rectangle([0, config_y, final_width, config_y + config_height], fill=(240, 240, 240))
            
            # 绘制标题
            if title:
                try:
                    draw.text((10, config_y + 5), title, fill=(0, 0, 0), font=font)
                except:
                    draw.text((10, config_y + 5), title, fill=(0, 0, 0))
            
            # 绘制配置信息
            if config_info:
                y_pos = config_y + 30
                for key, value in config_info.items():
                    text = f"{key}: {value}"
                    try:
                        draw.text((10, y_pos), text, fill=(70, 70, 70), font=small_font)
                    except:
                        draw.text((10, y_pos), text, fill=(70, 70, 70))
                    y_pos += 18
        else:  # left, right
            draw.rectangle([config_x, 0, config_x + config_width, final_height], fill=(240, 240, 240))
            
            # 绘制标题
            if title:
                try:
                    draw.text((config_x + 10, 5), title, fill=(0, 0, 0), font=font)
                except:
                    draw.text((config_x + 10, 5), title, fill=(0, 0, 0))
            
            # 绘制配置信息
            if config_info:
                y_pos = 30
                for key, value in config_info.items():
                    text = f"{key}: {value}"
                    try:
                        draw.text((config_x + 10, y_pos), text, fill=(70, 70, 70), font=small_font)
                    except:
                        draw.text((config_x + 10, y_pos), text, fill=(70, 70, 70))
                    y_pos += 18
    
    # 粘贴图片
    if direction == 'horizontal':
        x_offset = config_width if config_position == 'left' else 0
        for img in images:
            if output_format in ['JPEG', 'BMP', 'TIFF']:
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    background = Image.new('RGBA', img.size, (255, 255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background.convert('RGB')
            
            y_offset = config_height if config_position == 'top' else 0
            y_offset += (final_height - config_height - img.height) // 2
            merged_img.paste(img, (x_offset, y_offset))
            x_offset += img.width + spacing
    else:  # vertical
        y_offset = config_height if config_position == 'top' else 0
        for img in images:
            if output_format in ['JPEG', 'BMP', 'TIFF']:
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    background = Image.new('RGBA', img.size, (255, 255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background.convert('RGB')
            
            x_offset = config_width if config_position == 'left' else 0
            x_offset += (final_width - config_width - img.width) // 2
            merged_img.paste(img, (x_offset, y_offset))
            y_offset += img.height + spacing
    
    # 保存合并后的图片
    save_kwargs = {}
    if output_format == 'JPEG':
        save_kwargs['quality'] = 95
        save_kwargs['optimize'] = True
    elif output_format == 'GIF':
        save_kwargs['save_all'] = True
        if merged_img.mode != 'P':
            merged_img = merged_img.convert('P', palette=Image.ADAPTIVE)
    
    merged_img.save(output_path, format=output_format, **save_kwargs)
    print(f"带配置信息的合并完成，输出图片: {output_path} (格式: {output_format})")

# 示例用法
if __name__ == "__main__":
    # 示例图片路径（请替换为实际路径）
    image_paths = ["tpot_comparison.png", "throughput_comparison.png", "tpot_boxplot.png"]
    
    # 示例配置信息
    config = {
        "模型名称": "ResNet50",
        "批次大小": 32,
        "学习率": 0.001,
        "训练轮次": 100,
        "数据集": "CIFAR-10"
    }
    
    # 水平合并并添加配置信息
    merge_png_images_with_config(
        image_paths, 
     "merged_with_config.png", 
        config_info=config, 
        direction='horizontal', 
        spacing=10, 
        output_format='PNG'
    )
    
    # 网格合并并添加配置信息
    merge_png_grid_with_config(
        image_paths, 
        "grid_merged_with_config.jpg", 
        config_info=config, 
        rows=3, 
        cols=1, 
        output_format='JPEG'
    )
    
    # 自定义配置合并
    merge_with_custom_config(
        image_paths, 
        "custom_merged.png", 
        config_info=config, 
        title="实验结果对比", 
        direction='horizontal', 
        spacing=5, 
        output_format='PNG',
        config_position='top'
    )

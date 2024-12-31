from PIL import Image, ImageDraw, ImageFont
import os

def create_emoji_image(size):
    # Create a new image with a white background
    image = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    
    # Use a basic font size
    font_size = size
    try:
        # For macOS
        font = ImageFont.truetype('/System/Library/Fonts/Apple Color Emoji.ttc', font_size)
        
        # Draw the palm tree emoji
        draw.text((0, 0), '🌴', font=font, fill=(0, 0, 0))
        
        return image
    except Exception as e:
        print(f"Error creating image: {e}")
        return None

def main():
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'favicon')
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate different sizes
    sizes = [16, 32, 180]
    
    for size in sizes:
        img = create_emoji_image(size)
        if img:
            if size == 16:
                img.save(os.path.join(output_dir, 'favicon.ico'), format='ICO')
            elif size == 32:
                img.save(os.path.join(output_dir, 'favicon-32x32.png'), format='PNG')
            elif size == 180:
                img.save(os.path.join(output_dir, 'apple-touch-icon.png'), format='PNG')

if __name__ == '__main__':
    main()

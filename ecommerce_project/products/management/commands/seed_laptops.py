import io
import os
import random
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw, ImageFont

from products.models import Brand, Category, Product

LAPTOP_DATA = [
    {
        'name': 'MacBook Pro 16" M3 Max',
        'brand': 'Apple',
        'description': 'Apple M3 Max chip with 16-core CPU and 40-core GPU. 36GB unified memory, 1TB SSD. Stunning 16.2-inch Liquid Retina XDR display. Up to 22 hours of battery life.',
        'price': Decimal('3499.00'),
        'discount_price': Decimal('3199.00'),
        'stock': 15,
        'color': '#555555',
    },
    {
        'name': 'MacBook Air 15" M3',
        'brand': 'Apple',
        'description': 'Apple M3 chip with 8-core CPU and 10-core GPU. 16GB unified memory, 512GB SSD. 15.3-inch Liquid Retina display. Incredibly thin and light design.',
        'price': Decimal('1299.00'),
        'discount_price': None,
        'stock': 25,
        'color': '#C0C0C0',
    },
    {
        'name': 'Dell XPS 15',
        'brand': 'Dell',
        'description': 'Intel Core i9-13900H, 32GB DDR5 RAM, 1TB NVMe SSD. NVIDIA GeForce RTX 4060. 15.6-inch 3.5K OLED InfinityEdge display. Premium aluminum chassis.',
        'price': Decimal('2499.00'),
        'discount_price': Decimal('2199.00'),
        'stock': 10,
        'color': '#1a1a2e',
    },
    {
        'name': 'ThinkPad X1 Carbon Gen 11',
        'brand': 'Lenovo',
        'description': 'Intel Core i7-1365U vPro, 16GB LPDDR5 RAM, 512GB SSD. 14-inch 2.8K OLED display. Ultralight at just 2.48 lbs. MIL-STD-810H durability.',
        'price': Decimal('1899.00'),
        'discount_price': None,
        'stock': 20,
        'color': '#1C1C1C',
    },
    {
        'name': 'ASUS ROG Zephyrus G14',
        'brand': 'ASUS',
        'description': 'AMD Ryzen 9 7940HS, 16GB DDR5 RAM, 1TB SSD. NVIDIA GeForce RTX 4070. 14-inch QHD 165Hz display. Compact gaming powerhouse.',
        'price': Decimal('1999.00'),
        'discount_price': Decimal('1799.00'),
        'stock': 12,
        'color': '#0a0a0a',
    },
    {
        'name': 'HP Spectre x360 14',
        'brand': 'HP',
        'description': 'Intel Core i7-1355U, 16GB LPDDR4x RAM, 1TB SSD. 14-inch 2.8K OLED touch display. 360-degree hinge. Thunderbolt 4 ports. Pen support included.',
        'price': Decimal('1599.00'),
        'discount_price': None,
        'stock': 18,
        'color': '#2d3436',
    },
    {
        'name': 'Microsoft Surface Laptop 5',
        'brand': 'Microsoft',
        'description': 'Intel Core i7-1265U, 16GB LPDDR5x RAM, 512GB SSD. 13.5-inch PixelSense touchscreen. Alcantara palm rest. Elegant and portable design.',
        'price': Decimal('1499.00'),
        'discount_price': Decimal('1299.00'),
        'stock': 22,
        'color': '#E8E8E8',
    },
    {
        'name': 'Razer Blade 15',
        'brand': 'Razer',
        'description': 'Intel Core i7-13800H, 16GB DDR5 RAM, 1TB SSD. NVIDIA GeForce RTX 4070. 15.6-inch QHD 240Hz display. CNC aluminum unibody. Per-key RGB.',
        'price': Decimal('2699.00'),
        'discount_price': None,
        'stock': 8,
        'color': '#1a1a1a',
    },
    {
        'name': 'Lenovo IdeaPad Slim 7',
        'brand': 'Lenovo',
        'description': 'AMD Ryzen 7 7730U, 16GB DDR4 RAM, 512GB SSD. 16-inch WQXGA IPS display. Fingerprint reader. Backlit keyboard. 1080p webcam with shutter.',
        'price': Decimal('899.00'),
        'discount_price': Decimal('749.00'),
        'stock': 30,
        'color': '#4a4a4a',
    },
    {
        'name': 'Acer Swift 5',
        'brand': 'Acer',
        'description': 'Intel Core i7-1360P, 16GB LPDDR5 RAM, 512GB SSD. 14-inch 2.5K IPS touchscreen. Magnesium-lithium chassis weighs only 2.65 lbs. 10-hour battery.',
        'price': Decimal('1099.00'),
        'discount_price': None,
        'stock': 14,
        'color': '#6c5ce7',
    },
    {
        'name': 'Samsung Galaxy Book 3 Pro 360',
        'brand': 'Samsung',
        'description': 'Intel Core i7-1360P, 16GB LPDDR5 RAM, 1TB SSD. 16-inch AMOLED touchscreen. S Pen included. 360-degree hinge. Quad speakers AKG tuned.',
        'price': Decimal('1899.00'),
        'discount_price': Decimal('1649.00'),
        'stock': 10,
        'color': '#b2bec3',
    },
    {
        'name': 'Framework Laptop 16',
        'brand': 'Framework',
        'description': 'AMD Ryzen 7 7840HS, 32GB DDR5 RAM, 1TB NVMe SSD. Modular design with user-upgradeable GPU, expansion cards. 16-inch QHD+ 165Hz display.',
        'price': Decimal('2099.00'),
        'discount_price': None,
        'stock': 6,
        'color': '#2d2d2d',
    },
]


def generate_product_image(name, hex_color, size=(800, 600)):
    img = Image.new('RGB', size, hex_color)
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype("arial.ttf", 40)
        font_small = ImageFont.truetype("arial.ttf", 24)
    except (OSError, IOError):
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.rectangle([0, 0, size[0] - 1, size[1] - 1], outline='white', width=3)

    lines = name.split(' ', 3)
    label = ' '.join(lines[:3])
    bbox = draw.textbbox((0, 0), label, font=font_large)
    tw = bbox[2] - bbox[0]
    draw.text(
        ((size[0] - tw) // 2, size[1] // 2 - 60),
        label, fill='white', font=font_large
    )

    draw.text(
        (size[0] // 2 - 60, size[1] // 2 + 20),
        '💻 LAPTOP', fill='white', font=font_small
    )

    for _ in range(30):
        x = random.randint(0, size[0])
        y = random.randint(0, size[1])
        r = random.randint(1, 4)
        alpha = random.randint(20, 60)
        draw.ellipse(
            [x - r, y - r, x + r, y + r],
            fill=(255, 255, 255, alpha)
        )

    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    return ContentFile(buf.getvalue())


class Command(BaseCommand):
    help = 'Seed laptop products into the database'

    def handle(self, *args, **options):
        category, created = Category.objects.get_or_create(
            name='Laptops',
            defaults={'description': 'High-performance laptops for work, gaming, and everyday use.'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))
        else:
            self.stdout.write(f'Category already exists: {category.name}')

        brand_names = set(data['brand'] for data in LAPTOP_DATA)
        brands = {}
        for name in brand_names:
            brand, created = Brand.objects.get_or_create(
                name=name,
                defaults={'slug': name.lower()}
            )
            brands[name] = brand
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created brand: {brand.name}'))
            else:
                self.stdout.write(f'Brand already exists: {brand.name}')

        media_dir = Path(settings.MEDIA_ROOT) / 'products'
        media_dir.mkdir(parents=True, exist_ok=True)

        for i, data in enumerate(LAPTOP_DATA):
            slug = data['name'].lower().replace('"', '').replace("'", '').replace(' ', '-')[:200]

            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'category': category,
                    'brand': brands[data['brand']],
                    'name': data['name'],
                    'description': data['description'],
                    'price': data['price'],
                    'discount_price': data.get('discount_price'),
                    'stock': data['stock'],
                    'is_active': True,
                }
            )

            if created:
                image_content = generate_product_image(data['name'], data['color'])
                filename = f'{slug}.png'
                product.image.save(filename, image_content, save=True)
                self.stdout.write(self.style.SUCCESS(f'Created product: {product.name} (${product.price})'))
            else:
                if not product.image:
                    image_content = generate_product_image(data['name'], data['color'])
                    filename = f'{slug}.png'
                    product.image.save(filename, image_content, save=True)
                self.stdout.write(f'Updated product: {product.name}')

        self.stdout.write(self.style.SUCCESS(f'\nSeeded {len(LAPTOP_DATA)} laptop products successfully!'))

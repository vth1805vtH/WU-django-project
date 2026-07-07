def generate_description(product_name, brand, specs_list):
    specs_text = '\n'.join(f'- {s}' for s in specs_list if s.strip()) if specs_list else ''

    if brand:
        marketing = f'{brand} presents the {product_name} — a premium choice for your needs.'
    else:
        marketing = f'The {product_name} is a premium choice for your needs.'

    if specs_text:
        marketing += f' Featuring: {specs_list[0] if specs_list else ""}'

    marketing += ' Shop with confidence and enjoy quality you can trust.'

    features = specs_list if specs_list else ['High-quality build', 'Reliable performance']
    benefits = ['Durable and long-lasting', 'Great value for money']

    return {
        'marketing_description': marketing,
        'features': features[:6],
        'benefits': benefits,
    }

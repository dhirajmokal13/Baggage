def calculate_current_price(product):
    current_price = product.price - (product.price * product.discount / 100)
    rounded_price = round(current_price, 2)
    return rounded_price
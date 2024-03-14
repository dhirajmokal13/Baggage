from django import template
register = template.Library()

@register.simple_tag
def calculate_current_price(product):
    current_price = product.price - (product.price * product.discount / 100)
    rounded_price = round(current_price, 2)
    return rounded_price

@register.simple_tag
def rating_calc(rat):
    rating = ""
    filled_star = '<i class="fa fa-star rating-color"></i>'
    unfilled_star = '<i class="fa fa-star"></i>'
    for i in range(1, 5+1):
        if i<=rat:
            rating+=filled_star
            continue
        rating+=unfilled_star

    return rating